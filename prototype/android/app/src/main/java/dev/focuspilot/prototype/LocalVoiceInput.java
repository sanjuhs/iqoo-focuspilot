package dev.focuspilot.prototype;

import android.Manifest;
import android.content.Context;
import android.content.Intent;
import android.content.pm.PackageManager;
import android.os.Build;
import android.os.Bundle;
import android.os.Handler;
import android.os.Looper;
import android.speech.RecognitionListener;
import android.speech.RecognitionSupport;
import android.speech.RecognitionSupportCallback;
import android.speech.RecognizerIntent;
import android.speech.SpeechRecognizer;
import java.util.ArrayList;
import java.util.List;
import java.util.Locale;

/** Push-to-talk on the main thread, only the API31+ on-device factory. No fallback or download. */
public final class LocalVoiceInput implements AutoCloseable {
    public interface Listener {
        void onStatus(String message);
        void onDraft(String text);
        void onChanged();
    }
    private final Context context;
    private final VoiceDraftState state;
    private final Listener listener;
    private final Handler main=new Handler(Looper.getMainLooper());
    private SpeechRecognizer recognizer;
    private long activeToken;
    private boolean closed;
    public LocalVoiceInput(Context context,VoiceDraftState state,Listener listener) {
        this.context=context;this.state=state;this.listener=listener;
    }
    public static boolean available(Context context) {
        if(Build.VERSION.SDK_INT<31)return false;
        try{return SpeechRecognizer.isOnDeviceRecognitionAvailable(context);}catch(RuntimeException ignored){return false;}
    }
    public void start() {
        requireMainThread();
        if(closed)return;
        if(!state.canStart()){listener.onStatus("Stop voice or wait for local inference before speaking.");return;}
        if(context.checkSelfPermission(Manifest.permission.RECORD_AUDIO)!=PackageManager.PERMISSION_GRANTED){listener.onStatus("Microphone permission is off. Tap Speak to request it, or type your command.");return;}
        if(Build.VERSION.SDK_INT<31||!available(context)){listener.onStatus("On-device speech is unavailable here. Type a command; no cloud fallback is used.");return;}
        final long token=state.begin(true,true);
        activeToken=token;
        try {
            releaseRecognizer();
            recognizer=SpeechRecognizer.createOnDeviceSpeechRecognizer(context);
            recognizer.setRecognitionListener(recognitionListener(token));
            listener.onStatus("Checking installed on-device English speech support…");listener.onChanged();
            String preferred=Locale.getDefault().getLanguage().equals("en")?Locale.getDefault().toLanguageTag():"en-US";
            if(Build.VERSION.SDK_INT>=33)checkSupport(token,preferred,false);
            else beginListening(token,preferred,"Android 31–32 has no language preflight API; local recognition may report a missing model.");
            main.postDelayed(()->{if(state.accepts(token)){cancel();listener.onStatus("Voice timed out. Tap Speak for a new local attempt, or type your command.");}},20000);
        }catch(RuntimeException error){fail(token,"On-device speech could not start. Type a command and check the installed speech service.");}
    }
    @android.annotation.TargetApi(33)
    private void checkSupport(long token,String language,boolean retried) {
        recognizer.checkRecognitionSupport(intent(language),context.getMainExecutor(),new RecognitionSupportCallback(){
            @Override public void onSupportResult(RecognitionSupport support){
                if(!state.accepts(token)||closed)return;
                List<String> installed=support.getInstalledOnDeviceLanguages();
                for(String tag:installed)if(normalize(tag).equalsIgnoreCase(normalize(language))){beginListening(token,normalize(language),"Installed local language verified.");return;}
                // An installed English locale is a local language choice, not a network fallback.
                if(!retried)for(String tag:installed)if(Locale.forLanguageTag(normalize(tag)).getLanguage().equals("en")){
                    try{checkSupport(token,normalize(tag),true);}catch(RuntimeException error){fail(token,"Local language support check failed. Type your command.");}return;}
                fail(token,"No installed on-device English model is ready. Configure offline speech in Android settings, then retry; this app downloads nothing. You can type instead.");
            }
            @Override public void onError(int error){if(!state.accepts(token)||closed)return;
                fail(token,error==SpeechRecognizer.ERROR_CANNOT_CHECK_SUPPORT?
                    "This speech service cannot verify local language support. Voice stays off; type your command.":errorMessage(error));}
        });
    }
    private Intent intent(String language){return new Intent(RecognizerIntent.ACTION_RECOGNIZE_SPEECH)
        .putExtra(RecognizerIntent.EXTRA_LANGUAGE_MODEL,RecognizerIntent.LANGUAGE_MODEL_FREE_FORM)
        .putExtra(RecognizerIntent.EXTRA_LANGUAGE,language).putExtra(RecognizerIntent.EXTRA_PREFER_OFFLINE,true)
        .putExtra(RecognizerIntent.EXTRA_PARTIAL_RESULTS,true).putExtra(RecognizerIntent.EXTRA_MAX_RESULTS,1);}
    private void beginListening(long token,String language,String supportNote){
        if(!state.listening(token)||closed)return;
        try{recognizer.startListening(intent(language));listener.onStatus("Listening locally · "+language+". Speak one short command. Tap Finish voice when done. "+supportNote);listener.onChanged();}
        catch(RuntimeException error){fail(token,"On-device microphone start failed. Check permission and the local speech service; typing still works.");}
    }
    public void finishListening(){requireMainThread();if(closed||recognizer==null)return;
        if(state.phase()!=VoiceDraftState.Phase.LISTENING)return;
        // End-of-speech and results callbacks retain their original request token.
        try{state.processing(activeToken);recognizer.stopListening();listener.onStatus("Finishing local voice transcription… Review the final draft before inference.");listener.onChanged();}
        catch(RuntimeException ignored){cancel();listener.onStatus("Voice stopped. Tap Speak to try again.");}
    }
    private RecognitionListener recognitionListener(long token){return new RecognitionListener(){
        @Override public void onReadyForSpeech(Bundle params){if(state.accepts(token)&&state.phase()==VoiceDraftState.Phase.LISTENING)listener.onStatus("Microphone ready · local speech only. Say your command; then review the draft.");}
        @Override public void onBeginningOfSpeech(){}
        @Override public void onRmsChanged(float rmsDb){}
        @Override public void onBufferReceived(byte[] buffer){} // Audio is never retained by the app.
        @Override public void onEndOfSpeech(){if(state.processing(token)){listener.onStatus("Processing speech locally… No command will run automatically.");listener.onChanged();}}
        @Override public void onError(int error){fail(token,errorMessage(error));}
        @Override public void onResults(Bundle results){String text=first(results);
            if(state.finish(token,text)){releaseRecognizer();main.removeCallbacksAndMessages(null);listener.onDraft(state.draft());listener.onStatus("Voice draft ready. Edit it if needed, then tap Understand command locally. Nothing executed.");listener.onChanged();}
            else if(state.accepts(token))fail(token,"No usable short transcript. Try a command under 500 characters, or type it.");}
        @Override public void onPartialResults(Bundle partial){String text=first(partial);if(state.acceptsPartial(token,text))listener.onStatus("Heard (unfinished): "+text+"\nWaiting for the final draft; nothing executed.");}
        @Override public void onEvent(int eventType,Bundle params){}
    };}
    private static String first(Bundle bundle){if(bundle==null)return null;ArrayList<String> results=bundle.getStringArrayList(SpeechRecognizer.RESULTS_RECOGNITION);return results==null||results.isEmpty()?null:results.get(0);}
    private static String normalize(String tag){return tag==null?"":tag.trim().replace('_','-');}
    private void fail(long token,String message){if(closed||!state.fail(token))return;releaseRecognizer();main.removeCallbacksAndMessages(null);listener.onStatus(message);listener.onChanged();}
    public void cancel(){requireMainThread();state.cancel();main.removeCallbacksAndMessages(null);releaseRecognizer();if(!closed)listener.onChanged();}
    private void releaseRecognizer(){SpeechRecognizer previous=recognizer;recognizer=null;if(previous!=null){try{previous.cancel();}catch(RuntimeException ignored){}try{previous.destroy();}catch(RuntimeException ignored){}}}
    @Override public void close(){requireMainThread();closed=true;state.destroy();main.removeCallbacksAndMessages(null);releaseRecognizer();}
    private static void requireMainThread(){if(Looper.myLooper()!=Looper.getMainLooper())throw new IllegalStateException("Voice control must run on the main thread");}
    private static String errorMessage(int error){switch(error){
        case SpeechRecognizer.ERROR_INSUFFICIENT_PERMISSIONS:return "Microphone permission was denied or revoked. Grant it in Android settings only if you want voice; typing still works.";
        case SpeechRecognizer.ERROR_LANGUAGE_NOT_SUPPORTED:return "This language is not supported by the installed local speech service. Type your command.";
        case SpeechRecognizer.ERROR_LANGUAGE_UNAVAILABLE:return "The on-device language model is missing. Configure offline speech in Android settings; this app downloads nothing.";
        case SpeechRecognizer.ERROR_SPEECH_TIMEOUT:return "No speech heard. Tap Speak for another local attempt, or type a command.";
        case SpeechRecognizer.ERROR_NO_MATCH:return "Speech was not clear enough. Tap Speak to retry, or type your command.";
        case SpeechRecognizer.ERROR_RECOGNIZER_BUSY:return "The local speech service is busy. Stop voice and try again shortly.";
        case SpeechRecognizer.ERROR_AUDIO:return "Microphone audio was unavailable. Check Android microphone access or type instead.";
        case SpeechRecognizer.ERROR_NETWORK:case SpeechRecognizer.ERROR_NETWORK_TIMEOUT:return "The on-device service reported a network error. Voice stopped; no cloud fallback was attempted.";
        default:return "On-device speech failed (code "+error+"). Type your command or try again; nothing executed.";
    }}
}
