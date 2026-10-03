package dev.focuspilot.prototype;

import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.Base64;
import java.util.HashSet;

/** Pure known-wording development validator calls; no model or execution tools. */
public final class UnitRegression {
    private static String b64(String value) {
        return Base64.getEncoder().encodeToString((value == null ? "" : value).getBytes(StandardCharsets.UTF_8));
    }

    private static String kind(UnitCommand.Proposal p) {
        if (!p.accepted) return "UNKNOWN";
        return switch (String.valueOf(p.intent)) {
            case "start_focus" -> "START_FOCUS";
            case "pause_focus" -> "PAUSE_FOCUS";
            case "alarm" -> "ALARM";
            case "timer" -> "TIMER";
            case "explain" -> "EXPLAIN";
            case "open_app" -> switch (String.valueOf(p.app)) {
                case "settings" -> "OPEN_SETTINGS";
                case "calculator" -> "OPEN_CALCULATOR";
                case "clock" -> "OPEN_CLOCK";
                default -> throw new IllegalStateException("Accepted app outside contract");
            };
            default -> throw new IllegalStateException("Accepted intent outside contract");
        };
    }

    public static void main(String[] args) throws Exception {
        if (args.length != 1) throw new IllegalArgumentException("One pinned input TSV required");
        Path path = Path.of(args[0]);
        if (!Files.isRegularFile(path) || Files.size(path) > 8 * 1024 * 1024)
            throw new IllegalArgumentException("Bounded TSV required");
        var lines = Files.readAllLines(path, StandardCharsets.UTF_8);
        if (lines.isEmpty() || lines.size() > 4096) throw new IllegalArgumentException("Bounded routes required");
        var ids = new HashSet<String>();
        for (String line : lines) {
            String[] fields = line.split("\t", -1);
            if (fields.length != 3 || !fields[0].matches("[A-Za-z0-9_-]{1,64}") || !ids.add(fields[0]) ||
                fields[2].isBlank() || fields[2].length() > 500 || fields[2].chars().anyMatch(c -> c < 32 || c == 127 || c == 0x2028 || c == 0x2029))
                throw new IllegalArgumentException("Malformed development route");
            byte[] json = Base64.getDecoder().decode(fields[1]);
            if (json.length > 2048) throw new IllegalArgumentException("Bounded mock response required");
        }
        for (String line : lines) {
            String[] fields = line.split("\t", -1);
            String response = new String(Base64.getDecoder().decode(fields[1]), StandardCharsets.UTF_8);
            UnitCommand.Proposal p = UnitCommand.validate(fields[2], response);
            String canonicalKind = kind(p);
            int hour = p.accepted ? p.hour : 0;
            int minute = p.accepted ? p.minute : 0;
            long seconds = p.accepted ? p.durationSeconds : 0;
            String app = p.accepted && "open_app".equals(String.valueOf(p.intent)) ? String.valueOf(p.app) : "";
            System.out.println(fields[0] + "\t" + p.accepted + "\t" + canonicalKind + "\t" + hour + "\t" + minute + "\t" + seconds + "\t" + app + "\t" + b64(p.canonicalJson()) + "\t" + b64(p.reason));
        }
    }
}
