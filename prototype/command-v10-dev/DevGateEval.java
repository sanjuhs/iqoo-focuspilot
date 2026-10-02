package dev.focuspilot.prototype;

import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.HashSet;

/** Calls snapshotted actual validators on entire original requests; no execution. */
public final class DevGateEval {
    public static void main(String[] args) throws Exception {
        if(args.length!=1)throw new IllegalArgumentException("Selected proposal TSV required");
        Path input=Path.of(args[0]);
        if(!Files.isRegularFile(input)||Files.size(input)>8*1024*1024)throw new IllegalArgumentException("Invalid selected input");
        var rows=Files.readAllLines(input,StandardCharsets.UTF_8);var ids=new HashSet<String>();
        if(rows.isEmpty()||rows.size()>4096)throw new IllegalArgumentException("Invalid row count");
        for(String row:rows){String[] f=row.split("\t",-1);
            if(f.length!=3||!f[0].matches("[A-Za-z0-9_-]{1,64}")||!ids.add(f[0])||!f[1].matches("start_focus|pause_focus|alarm|timer|open_app|explain|unknown")||f[2].isBlank()||f[2].length()>500||f[2].chars().anyMatch(c->c<32||c==127||c==0x2028||c==0x2029))throw new IllegalArgumentException("Invalid proposal input");}
        for(String row:rows){String[] f=row.split("\t",-1);ModelCommandGate.Proposal p=ModelCommandGate.validate(f[1],f[2]);
            System.out.println(f[0]+"\t"+p.kind+"\t"+p.hour+"\t"+p.minute+"\t"+p.seconds);}
    }
}
