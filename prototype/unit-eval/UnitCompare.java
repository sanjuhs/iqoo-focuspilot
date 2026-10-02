package dev.focuspilot.prototype;

import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.Base64;
import java.util.HashSet;

/** Host proposal comparison only. No Android context or tool execution. */
public final class UnitCompare {
    private static String encode(String s) {
        return Base64.getEncoder().encodeToString(s.getBytes(StandardCharsets.UTF_8));
    }
    private static String decode(String s) {
        byte[] bytes = Base64.getDecoder().decode(s);
        String value = new String(bytes, StandardCharsets.UTF_8);
        if (!encode(value).equals(s)) throw new IllegalArgumentException("Canonical UTF-8 base64 required");
        return value;
    }
    public static void main(String[] args) throws Exception {
        if (args.length != 2 || !(args[0].equals("seconds") || args[0].equals("units") || args[0].equals("raw")))
            throw new IllegalArgumentException("seconds|units|raw and selected TSV required");
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
            if (args[0].equals("seconds")) {
                StructuredCommand.Proposal p = StructuredCommand.validate(request, response);
                canonical = p.canonicalJson(); accepted = p.accepted; reason = p.reason;
            } else {
                UnitCommand.Proposal p = args[0].equals("raw") ? UnitCommand.parseResponse(response) : UnitCommand.validate(request, response);
                canonical = p.canonicalJson(); accepted = p.accepted; reason = p.reason;
            }
            System.out.println(fields[0] + "\t" + encode(canonical) + "\t" + accepted + "\t" + encode(reason));
        }
    }
}
