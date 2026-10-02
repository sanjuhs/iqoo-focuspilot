package dev.focuspilot.prototype;

import java.nio.charset.StandardCharsets;
import java.util.Base64;

/** Renders the immutable prompt adapter; never constructs a model or generates tokens. */
public final class PromptInventory {
    public static void main(String[] args) {
        if (args.length != 1) throw new IllegalArgumentException("Unique boundary marker required");
        System.out.println(Base64.getEncoder().encodeToString(
                LocalModel.renderPrompt(args[0]).getBytes(StandardCharsets.UTF_8)));
    }
}
