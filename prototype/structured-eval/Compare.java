package dev.focuspilot.prototype;

import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.Base64;
import java.util.HashSet;

/** Host proposal comparison only. No Android context or tool execution. */
public final class Compare {
    private static String encode(String s) {
        return Base64.getEncoder().encodeToString(s.getBytes(StandardCharsets.UTF_8));
    }
    private static String decode(String s) {
        byte[] bytes = Base64.getDecoder().decode(s);
        String value = new String(bytes, StandardCharsets.UTF_8);
        if (!encode(value).equals(s)) throw new IllegalArgumentException("Canonical UTF-8 base64 required");
        return value;
    }
    private static String baseline(String intent, String original) {
        ModelCommandGate.Proposal p = ModelCommandGate.validate(intent, original);
        switch (p.kind) {
            case START_FOCUS: return "{\"intent\":\"start_focus\",\"duration_seconds\":" + p.seconds + "}";
            case PAUSE_FOCUS: return "{\"intent\":\"pause_focus\"}";
            case ALARM: return "{\"intent\":\"alarm\",\"hour\":" + p.hour + ",\"minute\":" + p.minute + "}";
            case TIMER: return "{\"intent\":\"timer\",\"duration_seconds\":" + p.seconds + "}";
            case OPEN_SETTINGS: return "{\"intent\":\"open_app\",\"app\":\"settings\"}";
            case OPEN_CALCULATOR: return "{\"intent\":\"open_app\",\"app\":\"calculator\"}";
            case OPEN_CLOCK: return "{\"intent\":\"open_app\",\"app\":\"clock\"}";
            case EXPLAIN: return "{\"intent\":\"explain\"}";
            default: return "{\"intent\":\"unknown\"}";
        }
    }
    public static void main(String[] args) throws Exception {
        if (args.length != 2 || !(args[0].equals("baseline") || args[0].equals("structured")))
            throw new IllegalArgumentException("baseline|structured and selected TSV required");
        Path path = Path.of(args[1]);
        if (!Files.isRegularFile(path) || Files.size(path) > 1_000_000)
            throw new IllegalArgumentException("Bounded TSV required");
        var rows = Files.readAllLines(path, StandardCharsets.UTF_8);
        if (rows.isEmpty() || rows.size() > 200) throw new IllegalArgumentException("1-200 rows required");
        var ids = new HashSet<String>();
        for (String row : rows) {
            String[] fields = row.split("\t", -1);
            if (fields.length != 3 || !fields[0].matches("[A-Za-z0-9_-]{1,64}") || !ids.add(fields[0]))
                throw new IllegalArgumentException("Unique ID and two base64 fields required");
            String request = decode(fields[1]), response = decode(fields[2]);
            if (request.isBlank() || request.length() > 500 || response.length() > 2048)
                throw new IllegalArgumentException("Bounded request/response required");
            String canonical, reason;
            boolean accepted;
            if (args[0].equals("baseline")) {
                if (!response.matches("\\{\"intent\":\"(start_focus|pause_focus|alarm|timer|open_app|explain|unknown)\"\\}"))
                    throw new IllegalArgumentException("Exact original intent response required");
                String intent = response.substring(11, response.length() - 2);
                canonical = baseline(intent, request);
                accepted = !canonical.equals("{\"intent\":\"unknown\"}");
                reason = accepted ? "Original gate accepted proposal" : "Original gate refused proposal";
            } else {
                StructuredCommand.Proposal p = StructuredCommand.validate(request, response);
                canonical = p.canonicalJson(); accepted = p.accepted; reason = p.reason;
            }
            System.out.println(fields[0] + "\t" + encode(canonical) + "\t" + accepted + "\t" + encode(reason));
        }
    }
}
