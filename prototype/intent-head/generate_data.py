"""Authored synthetic families for a separate learned hidden-state intent classifier."""
import hashlib,json,pathlib
INTENTS=['start_focus','pause_focus','alarm','timer','open_app','explain','unknown']
# Whole templates assigned to splits, not random rows; no labels from prior evaluations.
TEMPLATES={
 'train':{
 'start_focus':['Please activate {target} for {duration} minutes.','I need to begin {target} for {duration} minutes.','Let us start {target} for {duration} minutes.','Mira, resume {target} for {duration} minutes.','I would like to concentrate for {duration} minutes.','Start a {duration} minute {target} session.'],
 'pause_focus':['Pause the {target} session, please.','I want to halt my {target} session.','Could you cancel {target} mode?','Please end the current {target} session.','Let us stop {target} mode.','Mira, finish my {target} session.'],
 'alarm':['Add an alarm at {time}.','Please schedule an alarm for {time}.','I would like to wake me at {time}.','Mira, set my alarm to {time}.','Start an alarm for {time}, please.','Help me create an alarm at {time}.'],
 'timer':['Create a {duration} minute countdown, please.','Mira, begin a timer of {duration} minutes.','I need to set a {duration} minute timer.','Please start a timer lasting {duration} minutes.','Let us create a countdown for {duration} minutes.','Help me begin a {duration} minute countdown.'],
 'open_app':['Would you launch {app}, please?','Mira, show the {app} application.','Let us open {app} now.','Please help me launch {app}.','I would like to go to {app}.','Could you open the {app} screen?'],
 'explain':['Tell me about my {info}.','Could you explain the {info}, please?','What is my {info} now?','Display my {info}, please.','Mira, explain my {info}.','Help me understand the {info}.'],
 'unknown':['Never start {target} for {duration} minutes.','If I finish lunch, begin {target} for {duration} minutes.','Launch {unsupported_app} right away.','Cancel the alarm at {time}, please.','Start {target} for {duration} minutes, then open {app}.','Explain the weather in {city}.']},
 'validation':{
 'start_focus':['Can you please activate {target} for {duration} minutes now?','I would like a {duration} minute period of {target}.'],
 'pause_focus':['Would you please pause {target} mode now?','Stop my active {target} block, please.'],
 'alarm':['I need you to set an alarm for {time}, please.','Wake me up at {time}.'],
 'timer':['Would you start a countdown for {duration} minutes?','Please give me a {duration} minute timer.'],
 'open_app':['Mira, can you open {app} please?','I need to launch the {app} application.'],
 'explain':['Please show the {info}.','Tell me what my {info} means.'],
 'unknown':['Avoid launching {app}.','Begin {target} only when my meeting ends.','Stop the countdown of {duration} minutes.','Open {app} and wake me at {time}.']},
 'heldout':{
 'start_focus':['Please help me activate {target} for {duration} minutes.','For the next {duration} minutes, let me concentrate.','Would you begin my {target} session for {duration} minutes?'],
 'pause_focus':['Mira, can you halt the {target} session?','End my ongoing {target} block.','Please take me out of {target} mode.'],
 'alarm':['Could you add a wake-up alarm at {time}?','I want to schedule an alarm ringing at {time}.','Please make an alarm for half past seven.'],
 'timer':['Mira, set the countdown to {duration} minutes.','Could you please create a {duration} minute timer?','I want a countdown of {duration} minutes for my tea.'],
 'open_app':['Please take me to {app}.','Would you please show the {app} app now?','Help me bring up {app}.'],
 'explain':['Could you display the {info} now?','How is my {info}?','Please explain the {info} to me.'],
 'unknown':['I do not want an alarm at {time}.','Unless I ask again, start {target}.','Dismiss the alarm for {time}.','Resume {target} and launch {app}.','Can you please launch {unsupported_app}?','What is the forecast for {city}?']}}
PARAMETERS={
 'train':[(3,4,5,'focus','settings','focus mode','Spotify','Delhi'),(11,6,10,'concentration','calculator','focus nudge','Slack','Pune'),(24,9,25,'study','clock','focus warning','TikTok','Kochi'),(36,12,35,'deep work','settings','concentration session','Netflix','Surat'),(48,15,40,'focus','calculator','study session','Maps','Jaipur'),(65,20,50,'study','clock','focus status','Messages','Mysuru')],
 'validation':[(7,2,13,'study','settings','focus summary','Discord','Mumbai'),(16,10,21,'focus','calculator','focus reminder','Camera','Bengaluru'),(29,18,46,'concentration','clock','concentration status','Photos','Chennai'),(54,23,52,'deep work','calculator','study status','Browser','Nagpur')],
 'heldout':[(6,1,12,'concentration','clock','focus status','Gmail','Indore'),(19,8,18,'deep work','settings','focus session','WhatsApp','Goa'),(33,17,44,'study','calculator','concentration session','YouTube','Guwahati'),(85,22,57,'focus','clock','study session','Instagram','Ranchi')]}
def checksum(raw):return hashlib.sha256(raw).hexdigest()
def generate(root):
 root=pathlib.Path(root);root.mkdir(parents=True,exist_ok=True);allrows=[];seen_texts=set();seen_templates=set();manifest={'schema':1,'synthetic_only':True,'family_split_rule':'Whole authored templates fixed by split before probe/training; no random row split. No prior evaluation labels used. Shared task/app classes necessarily recur.','splits':{}}
 for split,groups in TEMPLATES.items():
  rows=[]
  for intent,templates in groups.items():
   for index,template in enumerate(templates):
    assert template not in seen_templates;seen_templates.add(template);family=f'{split}/{intent}/{index}';local=set()
    for row_index,values in enumerate(PARAMETERS[split]):
     duration,hour,minute,target,app,info,unsupported_app,city=values
     text=template.format(duration=duration,time=f'{hour}:{minute:02d}',target=target,app=app,info=info,unsupported_app=unsupported_app,city=city)
     if text in local:continue
     local.add(text);assert text not in seen_texts,text;seen_texts.add(text)
     action={'start_focus':'START_FOCUS','pause_focus':'PAUSE_FOCUS','alarm':'ALARM','timer':'TIMER','open_app':{'settings':'OPEN_SETTINGS','calculator':'OPEN_CALCULATOR','clock':'OPEN_CLOCK'}[app],'explain':'EXPLAIN','unknown':'UNKNOWN'}[intent]
     seconds=duration*60 if intent in ['start_focus','timer'] else 0;h=hour if intent=='alarm' else 0;m=minute if intent=='alarm' else 0
     if split=='heldout' and intent=='alarm' and index==2:action='UNKNOWN';h=m=seconds=0
     r={'id':f'{split}-{intent}-{index}-{row_index}','split':split,'family':family,'utterance':text,'intent':intent,'expected_action':action,'hour':h,'minute':m,'seconds':seconds}
     rows.append(r);allrows.append(r)
  raw=''.join(json.dumps(r,sort_keys=True)+'\n' for r in rows).encode();(root/f'{split}.jsonl').write_bytes(raw);(root/f'{split}.tsv').write_text(''.join(r['id']+'\t'+r['utterance']+'\n' for r in rows))
  manifest['splits'][split]={'rows':len(rows),'families':len({r['family'] for r in rows}),'sha256':checksum(raw),'label_counts':{i:sum(r['intent']==i for r in rows) for i in INTENTS},'family_hashes':{g:checksum(''.join(json.dumps(r,sort_keys=True)+'\n' for r in rows if r['family']==g).encode()) for g in sorted({r['family'] for r in rows})}}
 raw=''.join(json.dumps(r,sort_keys=True)+'\n' for r in allrows).encode();(root/'all-cases.jsonl').write_bytes(raw);(root/'all-cases.tsv').write_text(''.join(r['id']+'\t'+r['utterance']+'\n' for r in allrows));manifest['all_sha256']=checksum(raw);manifest['all_rows']=len(allrows)
 return manifest
if __name__=='__main__':
 p=pathlib.Path(__file__).parent;m=generate(p/'build');m['generator_sha256']=checksum(pathlib.Path(__file__).read_bytes());(p/'data-manifest.json').write_text(json.dumps(m,indent=2)+'\n');print(json.dumps({s:{k:v for k,v in a.items() if k!='family_hashes'} for s,a in m['splits'].items()},indent=2))
