#!/usr/bin/env node
import net from 'net';
import crypto from 'crypto';
import fs from 'fs';

const pipe = process.env.CODEX_APP_TOOLS_PIPE_PATH;
if (!pipe) {
  console.error(JSON.stringify({ error: 'CODEX_APP_TOOLS_PIPE_PATH is not set in environment' }));
  process.exit(1);
}

function callTool(sock, reqId, tool, args) {
  return new Promise((resolve, reject) => {
    const msg = JSON.stringify({
      id: reqId,
      jsonrpc: '2.0',
      method: 'tools/call',
      params: {
        arguments: args,
        callerSource: 'codex',
        callId: 'mcp-call-' + crypto.randomUUID(),
        hostId: process.env.CODEX_APP_TOOLS_CALLER_HOST_ID || 'local',
        namespace: 'codex_app',
        threadId: process.env.CODEX_THREAD_ID,
        tool: tool,
        turnId: 'mcp-turn-' + reqId
      }
    });
    const buf = Buffer.from(msg, 'utf8');
    const frame = Buffer.alloc(4 + buf.length);
    frame.writeUInt32LE(buf.length, 0);
    buf.copy(frame, 4);
    let data = Buffer.alloc(0);
    const onData = (chunk) => {
      data = Buffer.concat([data, chunk]);
      if (data.length >= 4) {
        const len = data.readUInt32LE(0);
        if (data.length >= 4 + len) {
          sock.off('data', onData);
          try {
            const resp = JSON.parse(data.subarray(4, 4 + len).toString('utf8'));
            resolve(resp);
          } catch (err) {
            reject(err);
          }
        }
      }
    };
    sock.on('data', onData);
    sock.write(frame);
  });
}

function parseToolResultText(resp) {
  const items = resp?.result?.contentItems || [];
  for (const item of items) {
    if (item?.text) {
      try {
        return JSON.parse(item.text);
      } catch {
        return { rawText: item.text };
      }
    }
  }
  return null;
}

const mode = process.argv[2];
const payloadPath = process.argv[3];
if (!mode) {
  console.error('Usage: node codex_thread_bridge.mjs <list-projects|create-and-send|send|wait> [payload.json]');
  process.exit(1);
}

const payload = payloadPath ? JSON.parse(fs.readFileSync(payloadPath, 'utf8')) : {};

const sock = net.createConnection(pipe, async () => {
  try {
    let reqId = 1;
    const results = [];
    if (mode === 'list-projects') {
      const resp = await callTool(sock, reqId++, 'list_projects', {});
      results.push(parseToolResultText(resp) || resp);
    } else if (mode === 'create-and-send') {
      const projectId = payload.projectId;
      for (const t of payload.tasks) {
        const createResp = await callTool(sock, reqId++, 'create_thread', {
          title: t.title,
          prompt: t.prompt,
          target: {
            type: 'project',
            projectId: projectId,
            environment: { type: 'local' }
          }
        });
        const parsed = parseToolResultText(createResp) || {};
        const threadId = parsed.threadId;
        const hostId = parsed.hostId || 'local';
        let waitInitResp = null;
        let sendResp = null;
        if (threadId) {
          waitInitResp = await callTool(sock, reqId++, 'wait_threads', {
            targets: [{ threadId, hostId }],
            timeoutMs: 30000
          });
          sendResp = await callTool(sock, reqId++, 'send_message_to_thread', {
            threadId,
            hostId,
            prompt: t.prompt
          });
        }
        results.push({ id: t.id, threadId, hostId, createResp, waitInitResp, sendResp });
      }
    } else if (mode === 'send') {
      for (const t of payload.tasks) {
        const sendResp = await callTool(sock, reqId++, 'send_message_to_thread', {
          threadId: t.threadId,
          hostId: t.hostId || 'local',
          prompt: t.prompt
        });
        results.push({ id: t.id, threadId: t.threadId, sendResp });
      }
    } else if (mode === 'wait') {
      const waitResp = await callTool(sock, reqId++, 'wait_threads', {
        targets: payload.targets,
        timeoutMs: payload.timeoutMs ?? 60000
      });
      results.push(parseToolResultText(waitResp) || waitResp);
    }
    if (payload.outputPath) {
      fs.writeFileSync(payload.outputPath, JSON.stringify(results, null, 2), 'utf8');
    }
    console.log(JSON.stringify(results, null, 2));
  } catch (err) {
    console.error(JSON.stringify({ error: String(err) }));
    process.exitCode = 1;
  } finally {
    sock.destroy();
  }
});
