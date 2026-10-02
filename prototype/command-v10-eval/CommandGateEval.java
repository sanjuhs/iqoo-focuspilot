package dev.focuspilot.prototype;

import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.Base64;
import java.util.HashSet;

/** Calls the actual Java original-request validator; contains no execution tools. */
public final class CommandGateEval {
    public static void main(String[] args) throws Exception {
        if(args.length!=1) throw new IllegalArgumentException("Selected proposal TSV required");
        Path input=Path.of(args[0]);
        if(!Files.isRegularFile(input) || Files.size(input)>8*1024*1024)
            throw new IllegalArgumentException("Selected TSV must be a regular file at most 8 MiB");
        var rows=Files.readAllLines(input,StandardCharsets.UTF_8);
        if(rows.isEmpty() || rows.size()>4096) throw new IllegalArgumentException("Expected 1 to 4096 proposals");
        var ids=new HashSet<String>();
        for(String row:rows) {
            String[] fields=row.split("\t",-1);
            if(fields.length!=3 || !fields[0].matches("[A-Za-z0-9_-]{1,64}") || !ids.add(fields[0]) ||
                !fields[1].matches("start_focus|pause_focus|alarm|timer|open_app|explain|unknown") ||
                fields[2].isBlank() || fields[2].length()>500 || fields[2].chars().anyMatch(c->c<32 || c==127 || c==0x2028 || c==0x2029))
                throw new IllegalArgumentException("Invalid synthetic proposal input");
        }
        for(String row:rows) {
            String[] fields=row.split("\t",-1);
            ModelCommandGate.Proposal p=ModelCommandGate.validate(fields[1],fields[2]);
            System.out.println(fields[0]+"\t"+p.kind+"\t"+p.hour+"\t"+p.minute+"\t"+p.seconds+"\t"+
                Base64.getEncoder().encodeToString(p.preview.getBytes(StandardCharsets.UTF_8)));
        }
    }
}
