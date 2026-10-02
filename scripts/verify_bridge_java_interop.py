#!/usr/bin/env python3
"""Synthetic Java export → actual offline laptop consumer. No phone or user input."""
import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import tempfile

ROOT=Path(__file__).resolve().parents[1]
FIXTURE='''import dev.focuspilot.prototype.FocusDataExport;import java.util.*;
public class ExportFixture { public static void main(String[] args)throws Exception {
 FocusDataExport.Settings settings=new FocusDataExport.Settings("dev.focuspilot.fixture",60000,60000,180000,"0000000000000000000000000000000000000000000000000000000000000000",true,false);
 List<FocusDataExport.Record> records=new ArrayList<>();
 for(int i=0;i<3;i++)records.add(new FocusDataExport.Record(i+1,settings,new double[]{i*.4,i*.3,.2,.5,0,.1},i==0?FocusDataExport.Label.ALLOW:FocusDataExport.Label.NUDGE,1000,500,600,"REAL_OBSERVATION"));
 System.out.write(FocusDataExport.render(new FocusDataExport.Snapshot(2000,settings,100,1000,false,records)));
}}'''

def verify():
    source=ROOT/'prototype/android/app/src/main/java/dev/focuspilot/prototype/FocusDataExport.java'
    with tempfile.TemporaryDirectory(prefix='bridge-java-',dir=ROOT/'artifacts') as temporary:
        directory=Path(temporary);writer=directory/'ExportFixture.java';writer.write_text(FIXTURE)
        subprocess.run(['javac','-d',str(directory),str(source),str(writer)],check=True,capture_output=True)
        payload=subprocess.check_output(['java','-cp',str(directory),'ExportFixture'])
        selected=directory/'summary.json';selected.write_bytes(payload);digest=hashlib.sha256(payload).hexdigest()
        result=subprocess.run(['python3',str(ROOT/'prototype/bridge/review_export.py'),'--input',str(selected),'--expected-sha256',digest],check=True,capture_output=True,text=True)
        report=json.loads(result.stdout)
        if report['record_count']!=3 or report['context_count']!=1 or report['input_sha256']!=digest:
            raise RuntimeError('Export/consumer compatibility failed')
        return {'research_only':True,'input_provenance':'synthetic Java-renderer fixture, not actual app usage/export',
            'transport':'temporary local file; not Office Kit','java_export_source_sha256':hashlib.sha256(source.read_bytes()).hexdigest(),
            'input_bytes':len(payload),'input_sha256':digest,'parsed_records':report['record_count'],'context_groups':report['context_count'],
            'policy_checkpoint_sha256':report['policy']['checkpoint_sha256'],'phone_actions_executed':False,
            'officekit_transport_verified':False,'npu_verified':False,'cli_exit_code':result.returncode}

def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--output',type=Path,help='Optional explicit metadata destination; no raw fixture data is saved');args=parser.parse_args()
    record=verify();encoded=json.dumps(record,indent=2)+'\n'
    if args.output:args.output.write_text(encoded)
    else:print(encoded,end='')

if __name__=='__main__':main()
