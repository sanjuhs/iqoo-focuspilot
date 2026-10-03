#!/usr/bin/env python3
"""One explicit installed-v17 native diagnostic; never installs the target app.

Launch this CLI through a yieldable exec session (yield <= 1000 ms), poll it at
<= 60-second intervals. Child subprocesses are polled, not blocking communicate
calls: instrumentation has a 150-second host deadline and no automatic retry.
Reports contain synthetic text/tensor data and stay in ignored artifacts only.
"""
import argparse
import base64
import hashlib
import json
import math
import os
from pathlib import Path
import re
import subprocess
import sys
import tempfile
import time
import zipfile

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'scripts'))
sys.path.insert(0, str(ROOT / 'prototype/compatible-phone'))
from phone_model_smoke import PhoneLab, PACKAGE
from phone_reviewed_reset import snapshot, NATIVE
from phone_bundled_import import pinned, installed_sha
from package_bundled_apk import project_bytes, verified_certificate
import phone_replay as replay

APP_SHA = '05a3fae677d464195186acbf330bd9ceb53ba49d42d97463d2c1d29cc521953e'
RESTORE_SHA = 'b79a81444b0956639a54607153e99fe9367e555dde40b9c61267c1ad4cafd61b'
MODEL_SHA = '57d1997790d1744fba5b40a7317df71ea5e2acee28c47e78f0cce39c0703f8cf'
MODEL_BYTES = 563036064
APP_SOURCE = 'a4f7a15c66cc44361e0b811aa578497a6b1cc8f9'
TEST_PACKAGE = PACKAGE + '.test'
RUNNER_NAME = PACKAGE + '.UnitNativeIsolationInstrumentation'
RUNNER = TEST_PACKAGE + '/' + RUNNER_NAME
JAVA_BASE = 'prototype/android/app/src/main/java/dev/focuspilot/prototype/'
JAVA_NAMES = ('LocalModel','CompatibleUnitCommand','UnitCommand','StructuredCommand',
              'ModelCommandGate','CommandNumberWords','CompatibleActionRouter','CompatibleReviewState')
REQUESTS = ('Start focus for 20 seconds','Stop focus','Set an alarm for 07:30',
            'Set a five-minute timer','Open calculator','Do not open settings')
RAW_GOLD = ({'intent':'start_focus','amount':20,'unit':'seconds'}, {'intent':'pause_focus'},
            {'intent':'alarm','hour':7,'minute':30}, {'intent':'timer','amount':5,'unit':'minutes'},
            {'intent':'open_app','app':'calculator'}, {'intent':'unknown'})
TENSORS = {'ffn_out-0','ffn_out-11','ffn_out-23','result_norm'}


def sha(path):
    with Path(path).open('rb') as stream:
        return hashlib.file_digest(stream,'sha256').hexdigest()


def strict(text):
    def pairs(items):
        result={}
        for key,value in items:
            if key in result: raise ValueError('Duplicate JSON key')
            result[key]=value
        return result
    def nonfinite(value): raise ValueError('Nonfinite JSON number')
    return json.loads(text,object_pairs_hook=pairs,parse_constant=nonfinite)


def exact(actual,expected,label):
    # Python equality alone incorrectly accepts True as integer 1.
    if type(actual) is not type(expected): raise ValueError('Wrong type: '+label)
    if isinstance(expected,dict):
        if actual.keys()!=expected.keys(): raise ValueError('Wrong keys: '+label)
        for key in expected: exact(actual[key],expected[key],label+'.'+key)
    elif isinstance(expected,list):
        if len(actual)!=len(expected): raise ValueError('Wrong length: '+label)
        for a,b in zip(actual,expected): exact(a,b,label)
    elif actual!=expected: raise ValueError('Different value: '+label)


def finite(value,label,nonnegative=True):
    if type(value) not in (int,float) or not math.isfinite(value) or (nonnegative and value<0):
        raise ValueError('Invalid finite number: '+label)


def positive_int(value,label):
    if type(value) is not int or value<=0: raise ValueError('Positive integer required: '+label)


def canonical(raw):
    if not isinstance(raw,dict) or type(raw.get('intent')) is not str:
        raise ValueError('Structured response required')
    intent=raw['intent']
    if intent in ('start_focus','timer'):
        if set(raw)!= {'intent','amount','unit'} or type(raw['amount']) is not int:
            raise ValueError('Exact duration source fields required')
        amount,unit=raw['amount'],raw['unit']
        if unit=='none' and intent=='start_focus' and amount==0: seconds=0
        elif type(unit) is str and unit in ('seconds','minutes','hours') and amount>0:
            seconds=amount*{'seconds':1,'minutes':60,'hours':3600}[unit]
            if seconds>7200: raise ValueError('Duration exceeds bounded contract')
        else: raise ValueError('Invalid duration source quantity')
        return {'intent':intent,'duration_seconds':seconds}
    if intent=='alarm':
        if set(raw)!= {'intent','hour','minute'} or type(raw['hour']) is not int or type(raw['minute']) is not int or not (0<=raw['hour']<24 and 0<=raw['minute']<60):
            raise ValueError('Invalid alarm slots')
    elif intent=='open_app':
        if set(raw)!= {'intent','app'} or raw['app'] not in ('settings','calculator','clock'):
            raise ValueError('Invalid app slots')
    elif intent in ('pause_focus','explain','unknown'):
        if set(raw)!= {'intent'}: raise ValueError('Unexpected fields')
    else: raise ValueError('Unsupported intent')
    return dict(raw)


class UnsafeReport(ValueError): pass


def parse_report(raw):
    prefix='INSTRUMENTATION_RESULT: report_json='
    values=[line[len(prefix):] for line in raw.splitlines() if line.startswith(prefix)]
    if len(values)!=1: raise ValueError('One native report required')
    return strict(values[0])


def validate_report(raw,source_commit,sources,contracts,before):
    r=parse_report(raw)
    codes=[line for line in raw.splitlines() if line.startswith('INSTRUMENTATION_CODE:')]
    if codes!=['INSTRUMENTATION_CODE: -1']: raise ValueError('Successful terminal instrumentation code required')
    expected={'schema':'focuspilot.unit_native_isolation.v1','passed':True,'request_count':6,
              'completed_request_count':6,'watchdog_ms':120000,'watchdog_triggered':False,
              'model_unsafe':False,'model_closed':True,'model_loaded':True,'actions_executed':0,
              'failure_type':None,'source_commit':source_commit,'declared_source_sha256':sources,
              'installed_apk_sha256':APP_SHA,'native_sha256':NATIVE}
    for key,value in expected.items(): exact(r.get(key),value,key)
    for key in ('preferences_accessed','production_preferences_accessed','production_singleton_used',
                'services_started','ui_used','voice_used','network_settings_changed','permission_grants_changed',
                'airplane_mode_claim','npu_claim','causal_interpretation_claim','semantic_accuracy_is_infrastructure_pass_condition'):
        exact(r.get(key),False,key)
    positive_int(r.get('checks'),'checks')
    for key in ('java_model_load_ms','java_instrumentation_ms'): finite(r.get(key),key)
    if r['java_instrumentation_ms']>=120000: raise ValueError('Terminal runtime exceeds global runner bound')
    identity=r.get('identity',{})
    for key,value in {'target_package':PACKAGE,'test_package':TEST_PACKAGE,'process_name':PACKAGE,
                      'target_process_name':PACKAGE,'target_manifest_requests_internet':False,
                      'test_manifest_requests_internet':False,'target_context_process_internet_permission':-1}.items():
        exact(identity.get(key),value,'identity.'+key)
    for key in ('process_uid','process_pid','target_application_uid','test_application_uid'): positive_int(identity.get(key),key)
    exact(identity['process_uid'],identity['target_application_uid'],'target process UID')
    if identity['test_application_uid']==identity['process_uid']: raise ValueError('Distinct test UID required')
    probe=r.get('socket_probe',{})
    for key,value in {'api':'android.system.Os.socket','family':2,'type':1,'protocol':6,
                      'connect_attempted':False,'dns_used':False,'payload_sent':False,
                      'socket_creation_succeeded':False,'returned_fd_closed':False,
                      'socket_creation_denied':True,'permission_denial_proven':True,
                      'attempted_function':'socket','exception_type':'android.system.ErrnoException'}.items():
        exact(probe.get(key),value,'socket.'+key)
    if type(probe.get('permission_errno')) is not int or probe['permission_errno'] not in (1,13): raise ValueError('Direct permission errno required')
    finite(probe.get('elapsed_ms'),'socket elapsed')
    for phase in ('model_before','model_after'):
        m=r.get(phase,{})
        for key,value in {'filename':'qwen35.gguf','bytes':MODEL_BYTES,'verified_bytes':MODEL_BYTES,
                          'sha256':MODEL_SHA,'links':1,'regular_file':True,'inode':before['model']['inode']}.items():
            exact(m.get(key),value,phase+'.'+key)
        positive_int(m.get('device'),phase+' device');positive_int(m.get('mtime'),phase+' mtime');finite(m.get('verification_ms'),phase+' verification')
    for key in ('filename','bytes','inode','device','links','regular_file','mtime','sha256','verified_bytes'):
        exact(r['model_after'][key],r['model_before'][key],'unchanged model '+key)
    exact(r.get('apk_after'),r.get('apk_before'),'unchanged APK')
    apk=r.get('apk_before',{})
    for key,value in {'sha256':APP_SHA,'native_sha256':NATIVE,'native_entry':'lib/arm64-v8a/libfocuspilot_local.so'}.items(): exact(apk.get(key),value,'apk.'+key)
    for key in ('bytes','inode','device','native_bytes'): positive_int(apk.get(key),'apk '+key)
    rows=r.get('requests')
    if type(rows) is not list or len(rows)!=6: raise ValueError('Six sequential requests required')
    for index,row in enumerate(rows):
        capture=index==1; gold=canonical(RAW_GOLD[index]); contract=contracts[index]
        for key,value in {'id':'native-unit-'+str(index+1),'request':REQUESTS[index],'capture':capture,
                          'prompt_sha256':contract['prompt_sha256'],'grammar_sha256':contract['grammar_sha256'],
                          'illustrative_expected_raw':RAW_GOLD[index],'illustrative_expected':gold}.items(): exact(row.get(key),value,'request '+key)
        finite(row.get('java_request_ms'),'request duration')
        native=row.get('native_output')
        if type(native) is not dict or set(native)!= {'text','metrics','activations'}: raise ValueError('Exact native envelope required')
        exact(strict(row.get('native_output_json','')),native,'native envelope echo')
        text=native['text']; parsed=strict(text); raw_canonical=canonical(parsed)
        exact(row.get('raw_canonical'),raw_canonical,'raw canonical')
        for key,value in {'raw_intent_matches_illustration':parsed['intent']==RAW_GOLD[index]['intent'],
                          'raw_full_slots_match_illustration':parsed==RAW_GOLD[index],
                          'canonical_slots_match_illustration':raw_canonical==gold}.items(): exact(row.get(key),value,key)
        metrics=native['metrics']
        for key,value in {'reached_eos':True,'cpu_only':True,'capture_enabled':capture}.items(): exact(metrics.get(key),value,key)
        for key in ('context_setup_ms','prefill_ms','decode_ms','total_ms'): finite(metrics.get(key),key)
        for key in ('prompt_tokens','generated_tokens'): positive_int(metrics.get(key),key)
        if metrics['generated_tokens']>127 or metrics['prompt_tokens']>896 or metrics['prompt_tokens']+metrics['generated_tokens']>1024: raise ValueError('Native token bounds exceeded')
        activations=native['activations']
        if type(activations) is not list or len(activations)!=(4 if capture else 0): raise ValueError('Capture count differs')
        names=set()
        for a in activations:
            name=a.get('tensor')
            if name not in TENSORS or name in names: raise ValueError('Unexpected/duplicate tensor')
            names.add(name);exact(a.get('width'),1024,'activation width');positive_int(a.get('positions_in_chunk'),'activation positions')
            for key in ('mean','rms','min','max'): finite(a.get(key),key,False)
            if a['rms']<0 or a['min']>a['max']: raise ValueError('Invalid activation range')
            values=a.get('first_values')
            if type(values) is not list or len(values)!=8: raise ValueError('Eight observed values required')
            for value in values: finite(value,'observed activation',False)
        for name in ('checked_model','fast_local','product_pipeline'):
            p=row.get(name,{})
            if type(p.get('accepted')) is not bool: raise ValueError('Acceptance boolean required')
            c=p.get('canonical')
            try: exact(c,gold,'checked canonical');matches=True
            except ValueError: matches=False
            if p['accepted'] and not matches: raise UnsafeReport('Incorrect accepted complete slots: '+name)
            if p['accepted']:
                if c['intent']=='unknown': raise UnsafeReport('Accepted unknown is not a complete executable action')
                if p.get('origin') not in ('CHECKED_MODEL','FAST_LOCAL_REQUEST'): raise ValueError('Accepted origin differs')
            else:
                exact(p.get('origin'),'UNKNOWN','refused origin');exact(c,{'intent':'unknown'},'refused canonical')
            if name=='checked_model' and p['accepted']: exact(p['origin'],'CHECKED_MODEL',name)
            if name=='fast_local' and p['accepted']: exact(p['origin'],'FAST_LOCAL_REQUEST',name)
            exact(p.get('matches_illustration'),matches,'illustrative checked match')
        wanted=row['fast_local'] if row['fast_local']['accepted'] else row['checked_model']
        exact(row['product_pipeline'],wanted,'fast-first pipeline')
    return r


def polled(command,timeout,*,popen=subprocess.Popen,clock=time.monotonic,pause=time.sleep):
    """Temporary files prevent pipe deadlock; no blocking wait longer than one second."""
    with tempfile.TemporaryFile() as stdout, tempfile.TemporaryFile() as stderr:
        process=popen(list(map(str,command)),stdout=stdout,stderr=stderr)
        started=clock();timed_out=False
        while process.poll() is None:
            if clock()-started>=timeout:
                timed_out=True;process.kill()
                try: process.wait(timeout=1)
                except subprocess.TimeoutExpired: raise RuntimeError('ADB client did not terminate after kill')
                break
            pause(.1)
        stdout.seek(0);stderr.seek(0)
        return {'returncode':process.returncode,'timed_out':timed_out,
                'stdout':stdout.read().decode('utf-8','replace'),'stderr':stderr.read().decode('utf-8','replace'),
                'client_ms':(clock()-started)*1000}


def replace_test(lab,path,expected,allowed_current,attempts,run=polled):
    current=replay.test_sha(lab)
    if current not in allowed_current: raise RuntimeError('Unknown test APK left unchanged')
    if current==expected: return {'skipped_already_installed':True,'observed_sha256':current}
    result=run(lab.base+['install','-r',str(path)],45)
    attempts.append(result)
    # Inspect after BOTH timeout and nonzero exit. PackageManager may have committed.
    observed=replay.test_sha(lab)
    result['observed_sha256']=observed;result['owned_install_verified']=observed==expected
    if observed!=expected: raise RuntimeError('Single test replacement did not establish exact owned identity; no retry')
    return result


def restore_test(lab,new_sha,original_path,attempts,run=polled):
    current=replay.test_sha(lab)
    if current==RESTORE_SHA: return {'already_original':True,'observed_sha256':current}
    if current!=new_sha: raise RuntimeError('Unknown test APK preserved; restoration refused')
    return replace_test(lab,original_path,RESTORE_SHA,{new_sha},attempts,run)


def execute(lab,a,record,before,run=polled):
    uncertain=False
    try:
        if installed_sha(lab)!=APP_SHA or replay.test_sha(lab)!=RESTORE_SHA or snapshot(lab)!=before:
            raise RuntimeError('Protected installed baseline changed before test replacement')
        replace_test(lab,a.test_apk,a.test_sha,{RESTORE_SHA},record['install_attempts'],run)
        arguments={'source_commit':a.source,'declared_source_sha256_b64':base64.b64encode(json.dumps(a.source_hashes,sort_keys=True,separators=(',',':')).encode()).decode(),
                   'expected_app_sha256':APP_SHA,'expected_native_sha256':NATIVE,'expected_model_sha256':MODEL_SHA}
        command=lab.base+['shell','am','instrument','-r','-w']
        for key,value in arguments.items(): command+=['-e',key,value]
        uncertain=True;record['instrumentation_attempted']=True
        result=run(command+[RUNNER],150);record['instrumentation']=result
        try:
            r=parse_report(result['stdout']);record['native_report']=r
            count=r.get('completed_request_count')
            if type(count) is int and 0<=count<=6: record['reported_completed_request_count']=count
        except Exception: r={}
        uncertain=result['timed_out'] or r.get('model_closed') is not True or r.get('model_unsafe') is True or r.get('watchdog_triggered') is True
        if result['timed_out'] or result['returncode']!=0: raise RuntimeError('Bounded native instrumentation incomplete')
        try: record['native_report']=validate_report(result['stdout'],a.source,a.source_hashes,a.contracts,before)
        except UnsafeReport: uncertain=True;raise
        record['runtime_passed']=True;record['verified_completed_native_generations']=6
    except Exception as error:
        record['failure_type']=type(error).__name__;record['failure']=str(error)
    finally:
        if uncertain:
            record['force_stop_required']=True
            try:
                if installed_sha(lab)!=APP_SHA: raise RuntimeError('Changed target identity; own-app force-stop refused')
                lab.adb('shell','am','force-stop',PACKAGE)
                record['research_app_force_stopped']=True
            except Exception as error: record['force_stop_failure_type']=type(error).__name__
        try:
            record['test_restoration']=restore_test(lab,a.test_sha,a.restore_test_apk,record['restore_attempts'],run)
            record['original_test_restored']=replay.test_sha(lab)==RESTORE_SHA
        except Exception as error:
            record['cleanup_failure_type']=type(error).__name__;record['cleanup_failure']=str(error)
        # Check protected state even when restoration is unknown/failed.
        try:
            record['after']=snapshot(lab);record['protected_state_unchanged']=record['after']==before
            record['installed_app_sha256_after']=installed_sha(lab)
            record['target_unchanged']=record['installed_app_sha256_after']==APP_SHA
        except Exception as error: record['postflight_failure_type']=type(error).__name__
        record['passed']=bool(record.get('runtime_passed') and record.get('original_test_restored') and
                              record.get('protected_state_unchanged') and record.get('target_unchanged') and
                              not record.get('force_stop_failure_type'))
    return record


def git(*args): return subprocess.check_output(['git',*args],cwd=ROOT)


def source_bindings(source):
    if not re.fullmatch('[0-9a-f]{40}',source) or git('rev-parse','HEAD').decode().strip()!=source or git('status','--porcelain').strip():
        raise RuntimeError('Exact clean frozen HEAD required')
    app_commit=git('rev-parse',APP_SOURCE).decode().strip()
    paths=[JAVA_BASE+n+'.java' for n in JAVA_NAMES]+['prototype/compatible-native-phone/UnitNativeIsolationInstrumentation.java',
        'prototype/android/app/src/androidTest/java/dev/focuspilot/prototype/UnitNativeIsolationInstrumentation.java']
    sources={}
    for relative in paths:
        data=(ROOT/relative).read_bytes()
        if git('show',source+':'+relative)!=data: raise RuntimeError('Frozen source bytes differ')
        if relative.startswith(JAVA_BASE) and git('show',app_commit+':'+relative)!=data:
            raise RuntimeError('Installed target source attribution differs: '+relative)
        sources[relative]=hashlib.sha256(data).hexdigest()
    if sources[paths[-1]]!=sources[paths[-2]]: raise RuntimeError('Packaged Android test runner copy differs from owned source')
    dependencies=['prototype/compatible-native-phone/README.md','prototype/compatible-native-phone/protocol.json','prototype/android/app/build.gradle',
                  'prototype/android/app/src/androidTest/java/dev/focuspilot/prototype/LocalModelIsolationInstrumentation.java',
                  'prototype/compatible-native-phone/phone_probe.py','prototype/compatible-native-phone/test_phone_probe.py',
                  'prototype/compatible-phone/phone_replay.py','prototype/compatible-phone/generate_fixtures.py']
    dependencies += ['scripts/'+n for n in ('phone_model_smoke.py','phone_reviewed_reset.py','phone_bundled_import.py','phone_task_guide.py','phone_readback.py','package_bundled_apk.py')]
    helpers={}
    for relative in dependencies:
        data=(ROOT/relative).read_bytes()
        if git('show',source+':'+relative)!=data: raise RuntimeError('Frozen harness/helper bytes differ')
        helpers[relative]=hashlib.sha256(data).hexdigest()
    return app_commit,sources,helpers


def inspect_apks(light,test,restore,tools):
    certs=[verified_certificate(tools/'apksigner',p) for p in (light,test,restore)]
    if len(set(certs))!=1: raise ValueError('All own signing certificates must match')
    infos=[replay.manifest_info(replay.tool([tools/'aapt','dump','badging',p]),replay.tool([tools/'aapt','dump','xmltree',p,'AndroidManifest.xml'])) for p in (light,test,restore)]
    if (infos[0]['package'],infos[0]['version_code'],infos[0]['version_name'])!=(PACKAGE,'17','0.17-system-one-research'):
        raise ValueError('Exact v17 light target required')
    if any(i['package']!=TEST_PACKAGE for i in infos[1:]): raise ValueError('Own test packages required')
    if infos[1]['instrumentation']!=[{'name':RUNNER_NAME,'targetPackage':PACKAGE}]: raise ValueError('One exact native runner required')
    if 'android.permission.INTERNET' in infos[0]['permissions'] or any(i['permissions'] for i in infos[1:]): raise ValueError('No Internet target/new-test permissions required')
    with zipfile.ZipFile(light) as z:
        if len(z.namelist())!=len(set(z.namelist())) or any(n.endswith('.gguf') for n in z.namelist()): raise ValueError('Unique light APK required')
        if hashlib.sha256(z.read('lib/arm64-v8a/libfocuspilot_local.so')).hexdigest()!=NATIVE: raise ValueError('Pinned native differs')
        target_classes=replay.apk_classes(z)
    with zipfile.ZipFile(test) as z:
        if len(z.namelist())!=len(set(z.namelist())) or any(n.endswith('.gguf') or n.startswith('lib/') for n in z.namelist()): raise ValueError('Test must carry no native/model payload')
        test_classes=replay.apk_classes(z)
    descriptors=['L'+(PACKAGE+'.'+n).replace('.','/')+';' for n in JAVA_NAMES]
    if any(target_classes.count(n)!=1 for n in descriptors): raise ValueError('All target helpers defined exactly once required')
    overlap=set(target_classes)&set(test_classes)
    if overlap: raise ValueError('Test may not shadow ANY installed target DEX definition')
    runner='L'+RUNNER_NAME.replace('.','/')+';'
    if test_classes.count(runner)!=1: raise ValueError('Runner defined exactly once in test required')
    replay.tool([tools/'zipalign','-c','-P','16','4',light])
    return {'public_certificate_sha256':certs[0],'manifests':infos,'native_sha256':NATIVE,
            'target_class_definitions':descriptors,'test_target_dex_overlap':[],
            'source_attribution_limit':'Source hashes bind frozen build inputs, not Java source recovered from installed DEX.'}



def verify_protocol(protocol,sources):
    for key,value in {'schema':'focuspilot.compatible_native_phone_protocol.v1','research_only':True,
                      'prospective_protocol_before_outputs':True}.items():exact(protocol.get(key),value,key)
    rows=[{'id':'native-unit-'+str(i+1),'request':request,'capture':i==1,
           'expected_raw':RAW_GOLD[i],'expected':canonical(RAW_GOLD[i])} for i,request in enumerate(REQUESTS)]
    exact(protocol.get('requests'),rows,'prospective manual fixtures')
    target=protocol.get('selected_target',{})
    for key,value in {'application_package':PACKAGE,'test_package':TEST_PACKAGE,'version_code':17,
                      'version_name':'0.17-system-one-research','app_source_commit':APP_SOURCE,
                      'light_apk_sha256':APP_SHA,'original_test_apk_sha256':RESTORE_SHA,
                      'native_sha256':NATIVE,'model_filename':'qwen35.gguf','model_bytes':MODEL_BYTES,
                      'model_sha256':MODEL_SHA,'java_wrapper_sha256':sources[JAVA_BASE+'LocalModel.java'],
                      'compatible_command_sha256':sources[JAVA_BASE+'CompatibleUnitCommand.java']}.items(): exact(target.get(key),value,key)
    native=protocol.get('native_calls',{})
    for key,value in {'model_objects':1,'context':1024,'threads':4,'maximum_generated_samples':128,
                      'actual_generated_non_eog_tokens_range':[1,127],'maximum_actual_prompt_tokens':896,
                      'total_generation_calls':6,'generation_calls_per_request':1,'attempts':1,'retries':0,
                      'force_inference_even_if_fast_local_accepts':True,'output_driven_repairs_or_row_filtering':False}.items():exact(native.get(key),value,key)
    deadlines=protocol.get('deadlines_and_cleanup',{})
    for key,value in {'runner_global_watchdog_ms':120000,'host_instrumentation_timeout_seconds':150,
                      'test_restore_install_client_timeout_seconds':45}.items():exact(deadlines.get(key),value,key)
    request_source=protocol.get('request_source',{})
    exact(request_source.get('original_request_indices_zero_based'),[0,1,2,3,4,6],'seen source indices')
    path=request_source.get('path')
    if path!='prototype/android/app/src/androidTest/java/dev/focuspilot/prototype/LocalModelIsolationInstrumentation.java' or sha(ROOT/path)!=request_source.get('sha256'):
        raise ValueError('Prospective seen request source identity differs')
    return protocol

def rendered_contracts(source,java_home):
    """Pure prompt/grammar renderer only. No parser, model, inference or phone call."""
    java_home=Path(java_home).resolve()
    java_tool=java_home/'bin/java';javac_tool=java_home/'bin/javac'
    version=polled([java_tool,'-version'],10)
    if version['returncode']!=0 or version['timed_out'] or not re.search(r'(?:openjdk|java) version "17[."]',version['stdout']+version['stderr']):
        raise RuntimeError('Explicit JAVA_HOME Java17 runtime required')
    folder=ROOT/'prototype/compatible-native-phone/build'/('contracts-'+source)
    if folder.exists(): raise RuntimeError('New exact-source contract directory required; no overwrite')
    if subprocess.run(['git','check-ignore','-q',str(folder)],cwd=ROOT).returncode!=0: raise RuntimeError('Contract build must be ignored')
    folder.mkdir(parents=True)
    java=folder/'ContractHashes.java'
    java.write_text('''import dev.focuspilot.prototype.CompatibleUnitCommand;
import java.nio.charset.StandardCharsets;import java.security.MessageDigest;
public class ContractHashes {
 static String hash(String text)throws Exception {StringBuilder s=new StringBuilder();for(byte b:MessageDigest.getInstance("SHA-256").digest(text.getBytes(StandardCharsets.UTF_8)))s.append(String.format("%02x",b&255));return s.toString();}
 public static void main(String[] args)throws Exception {for(String text:args)System.out.println(hash(CompatibleUnitCommand.renderPrompt(text))+"\\t"+hash(CompatibleUnitCommand.GRAMMAR));}
}''')
    # LocalModel itself not initialized: renderer compiles only pure dependencies.
    pure=[ROOT/(JAVA_BASE+n+'.java') for n in JAVA_NAMES if n not in ('LocalModel','CompatibleReviewState')]
    replay.tool([javac_tool,'-d',folder,*pure,java])
    result=replay.tool([java_tool,'-cp',folder,'ContractHashes',*REQUESTS])
    lines=result.splitlines()
    if len(lines)!=6 or any(not re.fullmatch('[0-9a-f]{64}\t[0-9a-f]{64}',s) for s in lines): raise ValueError('Exact prompt/grammar hashes required')
    return [dict(zip(('prompt_sha256','grammar_sha256'),s.split('\t'))) for s in lines]


def main():
    p=argparse.ArgumentParser(description=__doc__)
    for key in ('serial','source','test-sha'): p.add_argument('--'+key,required=True)
    for key in ('test-apk','output'): p.add_argument('--'+key,required=True,type=Path)
    p.add_argument('--light',type=Path,default=ROOT/'artifacts/focuspilot-research-v017-system-one-light.apk')
    p.add_argument('--restore-test-apk',type=Path,default=ROOT/'artifacts/focuspilot-research-v013-reset-test.apk')
    p.add_argument('--tools',type=Path,default=Path.home()/'Library/Android/sdk/build-tools/36.0.0')
    p.add_argument('--java-home',type=Path,default=Path(os.environ['JAVA_HOME']) if 'JAVA_HOME' in os.environ else None)
    p.add_argument('--execute-own-unit-native-probe',action='store_true');a=p.parse_args()
    if a.java_home is None: p.error('Explicit --java-home or JAVA_HOME Java17 required')
    if not a.execute_own_unit_native_probe: p.error('Explicit own native probe flag required')
    if not re.fullmatch('[0-9a-f]{64}',a.test_sha) or a.test_sha in (APP_SHA,RESTORE_SHA): raise ValueError('New frozen own test SHA required')
    app_commit,a.source_hashes,helpers=source_bindings(a.source)
    protocol=verify_protocol(strict((ROOT/'prototype/compatible-native-phone/protocol.json').read_text()),a.source_hashes)
    out=a.output.resolve()
    if out.exists() or not out.is_relative_to(ROOT/'artifacts') or subprocess.run(['git','check-ignore','-q',str(out)],cwd=ROOT).returncode!=0:
        raise ValueError('New ignored private artifacts report required')
    for path,digest in ((a.light,APP_SHA),(a.test_apk,a.test_sha),(a.restore_test_apk,RESTORE_SHA)):
        if sha(path)!=digest: raise ValueError('Pinned local APK differs')
    inspection=inspect_apks(a.light,a.test_apk,a.restore_test_apk,a.tools)
    if project_bytes(ROOT)+20_000_000>15_000_000_000: raise RuntimeError('Native probe reservation exceeds15GB logical cap')
    a.contracts=rendered_contracts(a.source,a.java_home)
    lab=PhoneLab(a.serial);before=snapshot(lab)
    if before['checkpoint']['active'] is not False or before['checkpoint']['observation'] is not False or not before['services_absent'] or not pinned(before['model']) or installed_sha(lab)!=APP_SHA or replay.test_sha(lab)!=RESTORE_SHA:
        raise RuntimeError('Exact paused/off/services-absent/pinned-model/v17/original-test baseline required')
    record={'schema':'focuspilot.unit_native_phone_probe.v1','source_commit':a.source,'installed_app_source_commit':app_commit,
            'source_sha256':a.source_hashes,'helper_sha256':helpers,'protocol_sha256':helpers['prototype/compatible-native-phone/protocol.json'],
            'storage_reserve_bytes':20_000_000,'storage_reserve_note':'Conservative20MB reservation exceeds protocol10MB minimum.',
            'java_home':str(a.java_home.resolve()),'harness_sha256':sha(Path(__file__)),
            'app_sha256':APP_SHA,'test_sha256':a.test_sha,'original_test_sha256':RESTORE_SHA,'native_sha256':NATIVE,
            'contracts':a.contracts,'apk_inspection':inspection,'before':before,'install_attempts':[],'restore_attempts':[],
            'runtime_passed':False,'passed':False,'original_test_restored':False,'target_installed':False,
            'force_stop_required':False,'research_app_force_stopped':False,'requested_model_inference':True,
            'instrumentation_attempted':False,'verified_completed_native_generations':0,
            'reported_completed_request_count':None,
            'permission_grants':0,'ui_used':False,'phone_woken':False,
            'scope':'Six fixed seen requests through installed JNI unit API. No fresh accuracy, UI, action, NPU or causal interpretation claim.',
            'snapshot_scope':'Three preference-store semantic hashes/checkpoint; model full SHA/bytes/inode/links; RECORD_AUDIO and POST_NOTIFICATIONS runtime grants; two own service absence. Not all AppOps/settings.'}
    out.parent.mkdir(parents=True,exist_ok=True)
    with out.open('x') as stream: json.dump(record,stream,indent=2)
    try: execute(lab,a,record,before)
    finally:
        record['project_logical_bytes_after']=project_bytes(ROOT)
        out.write_text(json.dumps(record,indent=2)+'\n')
    print(json.dumps({key:record.get(key,False) for key in ('passed','runtime_passed','original_test_restored','protected_state_unchanged','target_unchanged','research_app_force_stopped')}))
    if not record['passed']: raise SystemExit(1)


if __name__=='__main__': main()
