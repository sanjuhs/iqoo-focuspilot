package dev.focuspilot.prototype;
import java.nio.charset.StandardCharsets;
import java.util.Base64;
public final class PromptInventory {
    public static void main(String[] args){
        if(args.length!=1)throw new IllegalArgumentException("Marker required");
        System.out.println(Base64.getEncoder().encodeToString(CompactIntentCandidate.renderPrompt(args[0]).getBytes(StandardCharsets.UTF_8)));
        System.out.println(Base64.getEncoder().encodeToString(CompactIntentCandidate.GRAMMAR.getBytes(StandardCharsets.UTF_8)));
        System.out.println(CompactIntentCandidate.MAX_TOKENS);
    }
}
