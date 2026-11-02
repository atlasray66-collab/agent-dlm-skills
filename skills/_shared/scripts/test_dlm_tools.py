"""Portable behavior regressions; all mutations are confined to temp fixtures."""
import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

HERE=Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location('doctor_test_target', HERE/'dlm_doctor.py')
doctor=importlib.util.module_from_spec(spec)
sys.modules[spec.name]=doctor
spec.loader.exec_module(doctor)

class PortableToolsTest(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root=Path(self.temp.name)
        self.doc=self.root/'doc_llm'
        self.task=self.write('doc_llm/Tasks/E001_fixture/subtasks/S001.md','')
        self.write('input.txt','fixture')
        self.content='''# S001: Fixture

## Meta

| 状态 | ACTIVE |
| 优先级 | P1 |
| 依赖 | 无 |

## History

| 状态 | DONE |

<context_manifest schema="2" project="portable" epic="E001" task="S001">
  <file path="input.txt" required="true" intent="input" />
</context_manifest>
'''
        self.task.write_text(self.content,encoding='utf-8')

    def write(self,path,text):
        file=self.root/path;file.parent.mkdir(parents=True,exist_ok=True)
        file.write_text(text,encoding='utf-8',newline='');return file

    def validate(self,text=None,legacy=False):
        report=doctor.Report(str(self.root))
        doctor.validate_manifest(self.task,text or self.content,self.root,self.doc,report,'portable',999 if legacy else 1,not legacy)
        return report

    def run_sync(self,name,*args):
        return subprocess.run([sys.executable,'-B','-X','utf8',str(HERE/name),'--repo-root',str(self.root),'--all',*args],encoding='utf-8',text=True,capture_output=True)

    def test_current_meta_does_not_read_historical_status(self):
        self.assertEqual('ACTIVE',doctor.extract_status(self.content))
        self.assertEqual('',doctor.extract_status('# S001\n\n## History\n| 状态 | DONE |'))

    def test_xml_is_complete_and_attributes_are_required(self):
        self.assertEqual([],self.validate().errors)
        for old,new in [('</context_manifest>',''),('intent="input"',''),('task="S001"','task="S009"'),('epic="E001"','epic="E002"'),('<file ','<wrong '),('required="true"','required="true" defer="true"')]:
            with self.subTest(new=new):self.assertTrue(self.validate(self.content.replace(old,new)).errors)

    def test_files_outside_manifest_cannot_satisfy_empty_manifest(self):
        file='  <file path="input.txt" required="true" intent="input" />'
        self.assertTrue(self.validate(self.content.replace(file,'')+'\n'+file).errors)

    def test_paths_are_concrete_and_contained(self):
        for path in ['../input.txt','C:/input.txt','/input.txt','*.txt']:
            with self.subTest(path=path):self.assertTrue(self.validate(self.content.replace('path="input.txt"',f'path="{path}"')).errors)

    def test_legacy_optional_identity_is_not_bulk_migration_requirement(self):
        content=self.content.replace(' epic="E001" task="S001"','')
        self.assertEqual([],self.validate(content,legacy=True).errors)

    def epic(self):
        self.write('doc_llm/dlm.json',json.dumps({'task_status':{'allowed':['ACTIVE','DONE']}}))
        path=self.write('doc_llm/Tasks/E001_fixture/README.md','# Epic\n\n## 子任务索引\n\nold\n\n## History\n\nKeep history.\n')
        path.write_bytes(b'\xef\xbb\xbf'+path.read_text(encoding='utf-8').replace('\n','\r\n').encode('utf-8'))
        return path

    def test_custom_contract_statuses_bom_crlf_and_idempotent_check(self):
        path=self.epic()
        result=self.run_sync('sync_epic_index.py');self.assertEqual(0,result.returncode,result.stdout)
        data=path.read_bytes();self.assertTrue(data.startswith(b'\xef\xbb\xbf'))
        self.assertNotIn(b'\n',data.replace(b'\r\n',b''))
        self.assertIn(b'ACTIVE',data)
        self.assertEqual(0,self.run_sync('sync_epic_index.py','--check').returncode)
        self.assertEqual(data,path.read_bytes())

    def test_later_invalid_epic_does_not_write_earlier_epic(self):
        path=self.epic();before=path.read_bytes()
        self.write('doc_llm/Tasks/E002_fixture/README.md','# Epic\n\n## 子任务索引\n\nold\n')
        self.write('doc_llm/Tasks/E002_fixture/subtasks/S001.md',self.content.replace('ACTIVE','INVALID'))
        self.assertNotEqual(0,self.run_sync('sync_epic_index.py').returncode)
        self.assertEqual(before,path.read_bytes())

    def test_later_invalid_domain_does_not_write_earlier_route(self):
        first=self.write('doc_llm/Domains/one/L1_one_router.md','# Route\r\n\r\n## 路由表\r\n\r\nold\r\n')
        self.write('doc_llm/Domains/one/L2_Modules/one.md','---\nstatus: ready\nmatch_globs:\n  - "src/*.java"\n---\n# Module\n')
        self.assertEqual(0,self.run_sync('sync_l1_route.py').returncode)
        before=first.read_bytes();self.assertNotIn(b'\n',before.replace(b'\r\n',b''))
        self.assertEqual(0,self.run_sync('sync_l1_route.py','--check').returncode)
        self.write('doc_llm/Domains/two/L1_two_router.md','# Route\n\n## 路由表\nold\n')
        self.write('doc_llm/Domains/two/L2_Modules/two.md','# Missing metadata\n')
        self.assertNotEqual(0,self.run_sync('sync_l1_route.py').returncode)
        self.assertEqual(before,first.read_bytes())

if __name__=='__main__':unittest.main()
