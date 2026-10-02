package dev.focuspilot.prototype;
import java.nio.charset.StandardCharsets;
import java.util.Base64;
public final class JsonInventory {
    public static void main(String[] args){
        if(args.length!=1)throw new IllegalArgumentException("Marker required");
        System.out.println(Base64.getEncoder().encodeToString(JsonIntentCandidate.renderPrompt(args[0]).getBytes(StandardCharsets.UTF_8)));
        System.out.println(Base64.getEncoder().encodeToString(JsonIntentCandidate.GRAMMAR.getBytes(StandardCharsets.UTF_8)));
        System.out.println(JsonIntentCandidate.MAX_TOKENS);
    }
}
