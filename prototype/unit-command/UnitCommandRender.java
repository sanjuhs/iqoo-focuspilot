package dev.focuspilot.prototype;

import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.Base64;
import java.util.HashSet;

/** Selected-file renderer only; no inference. */
public final class UnitCommandRender {
    public static void main(String[] args) throws Exception {
        if (args.length != 1) throw new IllegalArgumentException("Use --grammar or one selected requests TSV");
        if (args[0].equals("--grammar")) { System.out.print(UnitCommand.GRAMMAR); return; }
        Path path = Path.of(args[0]);
        if (!Files.isRegularFile(path) || Files.size(path) > 2_000_000) throw new IllegalArgumentException("Bounded selected TSV required");
        java.util.List<String> lines = Files.readAllLines(path, StandardCharsets.UTF_8);
        if (lines.isEmpty() || lines.size() > 112) throw new IllegalArgumentException("1..112 rows required");
        HashSet<String> seen = new HashSet<>();
        java.util.List<String> output = new java.util.ArrayList<>();
        for (String line : lines) {
            String[] fields = line.split("\t", -1);
            if (fields.length != 2 || !fields[0].matches("[A-Za-z0-9_-]{1,80}") || !seen.add(fields[0]))
                throw new IllegalArgumentException("Unique bounded id and single-line utterance required");
            output.add(fields[0] + "\t" + Base64.getEncoder().encodeToString(UnitCommand.renderPrompt(fields[1]).getBytes(StandardCharsets.UTF_8)));
        }
        for (String line : output) System.out.println(line);
    }
}
