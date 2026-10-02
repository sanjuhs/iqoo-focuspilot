package dev.focuspilot.prototype;

import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.Base64;
import java.util.HashSet;

/** Frozen synthetic host comparison. Generates JSON proposals, executes no action. */
public final class Capture {
    public static void main(String[] args) throws Exception {
        if (args.length != 3 || !(args[2].equals("baseline") || args[2].equals("candidate")))
            throw new IllegalArgumentException("Model, requests and arm required");
        if (!JsonIntentCandidate.GRAMMAR.equals(LocalModel.INTENT_GRAMMAR)
                || JsonIntentCandidate.MAX_TOKENS != 128)
            throw new IllegalArgumentException("Both arms require original seven-intent JSON grammar and 128 tokens");
        Path input = Path.of(args[1]);
        if (!Files.isRegularFile(input) || Files.size(input) > 1024 * 1024)
            throw new IllegalArgumentException("Bounded selected input required");
        var rows = Files.readAllLines(input, StandardCharsets.UTF_8);
        var ids = new HashSet<String>();
        if (rows.size() != 100) throw new IllegalArgumentException("Exactly frozen 100 rows required");
        for (String row : rows) {
            String[] f = row.split("\t", -1);
            if (f.length != 2 || !f[0].matches("[A-Za-z0-9_-]{1,64}") || !ids.add(f[0])
                    || f[1].isBlank() || f[1].length() > 500
                    || f[1].chars().anyMatch(c -> c < 32 || c == 127 || c == 0x2028 || c == 0x2029))
                throw new IllegalArgumentException("Invalid frozen request row");
        }
        long began = System.nanoTime();
        long handle = LocalModel.nativeInit(args[0], 1024, 4);
        try {
            System.out.println("LOAD\t" + (System.nanoTime() - began));
            for (String row : rows) {
                String[] f = row.split("\t", -1);
                String prompt = args[2].equals("candidate")
                        ? JsonIntentCandidate.renderPrompt(f[1]) : LocalModel.renderPrompt(f[1]);
                LocalModel.nativePrepare(handle);
                began = System.nanoTime();
                String raw = LocalModel.nativeGenerate(handle, prompt, LocalModel.INTENT_GRAMMAR, 128, false);
                System.out.println(f[0] + "\t" + (System.nanoTime() - began) + "\t"
                        + Base64.getEncoder().encodeToString(raw.getBytes(StandardCharsets.UTF_8)));
                System.out.flush();
            }
        } finally {
            LocalModel.nativeClose(handle);
        }
    }
}
