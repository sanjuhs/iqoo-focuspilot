package dev.focuspilot.prototype;
import java.io.BufferedReader;
import java.io.InputStreamReader;

/** JVM CLI uses actual Android pure policies; tab protocol has no Android dependencies. */
public final class FewShotParity {
    public static void main(String[] args) throws Exception {
        FewShotPolicy policy=new FewShotPolicy();FewShotPolicy.Gates gates=new FewShotPolicy.Gates(false,true,true,true,true,true);
        try(BufferedReader reader=new BufferedReader(new InputStreamReader(System.in))){String line;
            while((line=reader.readLine())!=null){String[] parts=line.split("\t");if(parts[0].equals("clear")){policy.clear();continue;}
                double[] x=new double[6];for(int i=0;i<6;i++)x[i]=Double.parseDouble(parts[i+2]);
                if(parts[0].equals("add")){policy.add(x,FewShotPolicy.Label.valueOf(parts[1]));continue;}
                FewShotPolicy.Evaluation result=policy.evaluate(x,gates);double sum=0;for(FewShotPolicy.Neighbor n:result.neighbors)sum+=n.nudgeContribution;
                System.out.println(parts[1]+"\t"+result.recommendation+"\t"+result.nudgeVote+"\t"+result.uncertainty+"\t"+sum+"\t"+TrainedPolicy.evaluate(x).score);
            }
        }
    }
}
