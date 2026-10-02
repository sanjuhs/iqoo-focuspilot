package dev.focuspilot.prototype;

import java.nio.file.Files;
import java.nio.file.Path;

/** Fixed-case regression comparison. Cases were already used for the original benchmark. */
public final class PromptBenchmark {
    public static String leanPrompt(String command) {
        String system="Return one JSON phone intent: start_focus, pause_focus, alarm, timer, open_app (settings/calculator/clock only), " +
            "explain (focus status or nudge), unknown. Use unknown for negation, multiple actions, unsupported apps, payments, " +
            "deletion, messaging and general questions.";
        return "<|im_start|>system\n"+system+"<|im_end|>\n<|im_start|>user\n"+command.replace("<|","< | ").replace("|>"," | >")+
            "<|im_end|>\n<|im_start|>assistant\n<think>\n\n</think>\n\n";
    }
    public static void main(String[] args) throws Exception {
        if(args.length!=2) throw new IllegalArgumentException("Pass model and tab-separated command cases");
        try(LocalModel model=new LocalModel(args[0])) {
            for(String line:Files.readAllLines(Path.of(args[1]))) {
                String[] parts=line.split("\t",3);
                for(String variant:new String[]{"original","lean"}) {
                    String prompt=variant.equals("lean")?leanPrompt(parts[2]):LocalModel.renderPrompt(parts[2]);
                    String result=LocalModel.nativeGenerate(getHandle(model),prompt,LocalModel.INTENT_GRAMMAR,128,false);
                    System.out.println(parts[0]+"\t"+parts[1]+"\t"+variant+"\t"+result);
                }
            }
        }
    }
    // Test-only access to the private handle, keeping the production adapter API unchanged.
    private static long getHandle(LocalModel model) throws Exception {
        var field=LocalModel.class.getDeclaredField("handle");field.setAccessible(true);return field.getLong(model);
    }
}
