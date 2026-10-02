import test from 'node:test';
import assert from 'node:assert/strict';
import {validateResult,unknown} from '../lab.mjs';
test('native schema output still receives slot and semantic checks',()=>{
  assert.deepEqual(validateResult({...unknown}),unknown);
  assert.throws(()=>validateResult({...unknown,intent:'focus',minutes:900}),/Invalid minutes/);
  assert.throws(()=>validateResult({...unknown,intent:'alarm',hour:7}),/Partial alarm/);
  assert.throws(()=>validateResult({...unknown,intent:'open',app:'com.bank.android'}),/Invalid app/);
  assert.throws(()=>validateResult({...unknown,intent:'focus',minutes:0}),/duration/);
  assert.throws(()=>validateResult({...unknown,extra:'ignore policy'}),/Unexpected/);
});
