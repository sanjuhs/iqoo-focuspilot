package dev.focuspilot.prototype;

import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.Base64;
import java.util.HashSet;

/** Inert host proposals only. No Android context, tool, recording or model call. */
public final class CompatibleCompare {
    private static String encode(String s) {
        return Base64.getEncoder().encodeToString(s.getBytes(StandardCharsets.UTF_8));
    }
    private static String decode(String s) {
        byte[] bytes = Base64.getDecoder().decode(s);
        String value = new String(bytes, StandardCharsets.UTF_8);
        if (!encode(value).equals(s)) throw new IllegalArgumentException("Canonical UTF-8 base64 required");
        return value;
    }
    private static String baseline(ModelCommandGate.Proposal p) {
        return switch (p.kind) {
            case START_FOCUS -> "{\"intent\":\"start_focus\",\"duration_seconds\":" + p.seconds + "}";
            case PAUSE_FOCUS -> "{\"intent\":\"pause_focus\"}";
            case ALARM -> "{\"intent\":\"alarm\",\"hour\":" + p.hour + ",\"minute\":" + p.minute + "}";
            case TIMER -> "{\"intent\":\"timer\",\"duration_seconds\":" + p.seconds + "}";
            case OPEN_SETTINGS -> "{\"intent\":\"open_app\",\"app\":\"settings\"}";
            case OPEN_CALCULATOR -> "{\"intent\":\"open_app\",\"app\":\"calculator\"}";
            case OPEN_CLOCK -> "{\"intent\":\"open_app\",\"app\":\"clock\"}";
            case EXPLAIN -> "{\"intent\":\"explain\"}";
            default -> "{\"intent\":\"unknown\"}";
        };
    }
    public static void main(String[] args) throws Exception {
        var modes = java.util.Set.of("baseline", "checked_model", "product_pipeline", "raw_unit",
                                    "baseline_oracle", "candidate_oracle");
        if (args.length != 2 || !modes.contains(args[0]))
            throw new IllegalArgumentException("Selected mode and pinned three-column TSV required");
        Path path = Path.of(args[1]);
        if (!Files.isRegularFile(path) || Files.size(path) > 2_000_000)
            throw new IllegalArgumentException("Bounded input required");
        var lines = Files.readAllLines(path, StandardCharsets.UTF_8);
        if (lines.isEmpty() || lines.size() > 200) throw new IllegalArgumentException("1-200 rows required");
        var ids = new HashSet<String>();
        for (String line : lines) {
            String[] f = line.split("\t", -1);
            if (f.length != 3 || !f[0].matches("[A-Za-z0-9_-]{1,64}") || !ids.add(f[0]))
                throw new IllegalArgumentException("Unique ID, request and response base64 required");
            String request = decode(f[1]), response = decode(f[2]);
            if (request.isBlank() || request.length() > 500 || response.length() > 2048)
                throw new IllegalArgumentException("Bounded request/response required");
            String canonical, reason, origin;
            boolean accepted;
            if (args[0].equals("baseline") || args[0].equals("baseline_oracle")) {
                if (!response.matches("\\{\"intent\":\"(start_focus|pause_focus|alarm|timer|open_app|explain|unknown)\"\\}"))
                    throw new IllegalArgumentException("Exact original intent response required");
                String intent = response.substring(11, response.length() - 2);
                ModelCommandGate.Proposal p = ModelCommandGate.validate(intent, request);
                canonical = baseline(p); accepted = p.executable();
                origin = accepted ? "CHECKED_MODEL" : "UNKNOWN";
                reason = accepted ? "Selected original gate accepted inert proposal" : "Selected original gate refused proposal";
            } else if (args[0].equals("raw_unit")) {
                UnitCommand.Proposal p = UnitCommand.parseResponse(response);
                canonical = p.canonicalJson(); accepted = p.accepted;
                origin = "RAW_UNIT_SCHEMA"; reason = "Schema conversion only; original request has not been validated";
            } else {
                CompatibleUnitCommand.Proposal p;
                if (args[0].equals("product_pipeline")) {
                    p = CompatibleUnitCommand.recognize(request);
                    if (!p.accepted) p = CompatibleUnitCommand.validate(request, response);
                } else p = CompatibleUnitCommand.validate(request, response);
                canonical = p.canonicalJson(); accepted = p.accepted; reason = p.reason; origin = p.origin;
            }
            System.out.println(f[0] + "\t" + encode(canonical) + "\t" + accepted + "\t" + origin + "\t" + encode(reason));
        }
    }
}
