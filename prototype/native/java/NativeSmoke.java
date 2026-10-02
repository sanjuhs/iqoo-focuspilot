package dev.focuspilot.prototype;

import java.util.concurrent.atomic.AtomicReference;

/** Real JNI smoke test for the pinned host build, not a fake inference fixture. */
public final class NativeSmoke {
    public static void main(String[] args) throws Exception {
        if(args.length!=1) throw new IllegalArgumentException("Pass the verified local Qwen3.5 GGUF path");
        try(LocalModel model=new LocalModel(args[0])) {
            String normal=model.generateIntent("Start a focus session for 25 minutes.",false);
            if(!normal.contains("start_focus") || !normal.contains("\"reached_eos\":true")) throw new AssertionError(normal);
            String captured=model.generateIntent("Start a focus session for 25 minutes.",true);
            if(!captured.contains("ffn_out-0") || !captured.contains("result_norm") || !captured.contains("start_focus")) throw new AssertionError(captured);
            model.prepareGeneration();
            model.cancel(); // Deterministic reproduction: cancel before the queued task enters JNI.
            try {
                model.generatePreparedIntent("Start a focus session for 25 minutes.",false);
                throw new AssertionError("Pre-entry cancellation was lost");
            } catch(IllegalStateException error) {
                if(!error.getMessage().contains("cancelled before start")) throw error;
            }
            String fresh=model.generateIntent("Start a focus session for 25 minutes.",false);
            if(!fresh.contains("start_focus")) throw new AssertionError("Fresh request after pre-entry cancellation failed");
            AtomicReference<Throwable> outcome=new AtomicReference<>();
            model.prepareGeneration();
            Thread worker=new Thread(()->{try{model.generatePreparedIntent("Start a focus session for 25 minutes.",false);}catch(Throwable error){outcome.set(error);}});
            worker.start();Thread.sleep(100);model.cancel();worker.join(10000);
            if(worker.isAlive()) throw new AssertionError("Cancellation did not terminate the worker");
            if(outcome.get()==null || !outcome.get().getMessage().toLowerCase().contains("cancel")) throw new AssertionError("Expected cancellation",outcome.get());
            String afterCancel=model.generateIntent("Start a focus session for 25 minutes.",false);
            if(!afterCancel.contains("start_focus")) throw new AssertionError("Fresh-memory generation after cancellation failed");
        }
        LocalModel.nativeClose(0);
        LocalModel.nativeCancel(0);
        System.out.println("Real JNI inference, activation observation, pre-entry and in-flight cancellation, fresh request recovery, memory reset and idempotent closed-handle operations passed.");
    }
}
