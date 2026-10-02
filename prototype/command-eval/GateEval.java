package dev.focuspilot.prototype;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.Base64;
/** Calls the exact current app's pure Java gate; no duplicated validator. */
public final class GateEval {
 public static void main(String[] args) throws Exception {
  for(String line:Files.readAllLines(Path.of(args[0]))) {
   String[] f=line.split("\t",3);String command=new String(Base64.getDecoder().decode(f[2]),StandardCharsets.UTF_8);
   ModelCommandGate.Proposal p=ModelCommandGate.validate(f[1],command);
   System.out.println(f[0]+"\t"+p.kind+"\t"+p.hour+"\t"+p.minute+"\t"+p.seconds+"\t"+Base64.getEncoder().encodeToString(p.preview.getBytes(StandardCharsets.UTF_8)));
  }
 }
}
