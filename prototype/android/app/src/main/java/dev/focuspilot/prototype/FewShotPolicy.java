package dev.focuspilot.prototype;

import java.util.ArrayList;
import java.util.Collections;
import java.util.Comparator;
import java.util.List;

/** Local manual-example retrieval, not neural-network fine-tuning. No Android APIs or actions. */
public final class FewShotPolicy {
    public static final int MAX_EXAMPLES = 32;
    public static final int NEIGHBORS = 3;
    public static final double MAX_DISTANCE = 0.25;
    public static final double ALLOW_THRESHOLD = 0.35;
    public static final double NUDGE_THRESHOLD = 0.65;
    public enum Label { ALLOW, NUDGE }
    public enum Recommendation { BLOCKED, ABSTAIN, ALLOW, NUDGE }
    private final List<Example> examples = new ArrayList<>();
    private long nextId = 1;

    public static final class Example {
        public final long id;
        public final Label label;
        private final double[] features;
        public Example(long id, double[] features, Label label) {
            if(id < 1 || label == null) throw new IllegalArgumentException("Positive ID and a label required");
            this.id=id;this.features=validate(features);this.label=label;
        }
        public double[] features() { return features.clone(); }
    }
    public static final class Gates {
        public final boolean paused, consent, permission, activeFocus, fresh, cooldownReady;
        public Gates(boolean paused, boolean consent, boolean permission, boolean activeFocus, boolean fresh, boolean cooldownReady) {
            this.paused=paused;this.consent=consent;this.permission=permission;
            this.activeFocus=activeFocus;this.fresh=fresh;this.cooldownReady=cooldownReady;
        }
        public String blockedReason() {
            if(paused) return "Paused";
            if(!consent) return "Consent disabled";
            if(!permission) return "Required permission unavailable";
            if(!activeFocus) return "No active focus session";
            if(!fresh) return "Observation is missing or stale";
            if(!cooldownReady) return "Nudge cooldown is active";
            return null;
        }
    }
    public static final class Neighbor {
        public final long id;
        public final Label label;
        /** RMS distance over six normalized dimensions. */
        public final double distance;
        /** Normalized vote weight and exact additive contribution to nudgeVote. */
        public final double voteWeight, nudgeContribution;
        private final double[] features, squaredDistanceContributions;
        private Neighbor(Example example, double[] query, double distance, double weight) {
            id=example.id;label=example.label;features=example.features();this.distance=distance;
            voteWeight=weight;nudgeContribution=label==Label.NUDGE?weight:0;
            squaredDistanceContributions=new double[6];
            for(int i=0;i<6;i++) squaredDistanceContributions[i]=Math.pow(query[i]-features[i],2)/6;
        }
        public double[] features() { return features.clone(); }
        /** Sum equals distance squared; these explain similarity, not causal productivity effects. */
        public double[] squaredDistanceContributions() { return squaredDistanceContributions.clone(); }
    }
    public static final class Evaluation {
        public final Recommendation recommendation;
        public final String reason;
        /** Weighted label vote, not a calibrated probability. */
        public final double nudgeVote;
        /** Heuristic ambiguity/distance index, not a confidence interval. */
        public final double uncertainty;
        public final List<Neighbor> neighbors;
        private Evaluation(Recommendation recommendation, String reason, double vote, double uncertainty, List<Neighbor> neighbors) {
            this.recommendation=recommendation;this.reason=reason;this.nudgeVote=vote;this.uncertainty=uncertainty;
            this.neighbors=Collections.unmodifiableList(new ArrayList<>(neighbors));
        }
    }

    public synchronized Example add(double[] features, Label label) {
        Example example=new Example(nextId,features,label);
        if(nextId==Long.MAX_VALUE) throw new IllegalStateException("Example ID exhausted");
        nextId++;
        if(examples.size()==MAX_EXAMPLES) examples.remove(0);
        examples.add(example);return example;
    }
    /** Restore all-or-nothing; malformed or duplicate records never partially replace the store. */
    public synchronized void restore(List<Example> records) {
        if(records==null || records.size()>MAX_EXAMPLES) throw new IllegalArgumentException("At most 32 records required");
        List<Example> copy=new ArrayList<>();long maximum=0;
        for(Example record:records) {
            if(record==null || record.id==Long.MAX_VALUE) throw new IllegalArgumentException("Invalid record");
            for(Example prior:copy) if(prior.id==record.id) throw new IllegalArgumentException("Duplicate example ID");
            copy.add(new Example(record.id,record.features(),record.label));maximum=Math.max(maximum,record.id);
        }
        examples.clear();examples.addAll(copy);nextId=maximum+1;
    }
    public synchronized List<Example> examples() { return Collections.unmodifiableList(new ArrayList<>(examples)); }
    public synchronized boolean delete(long id) { return examples.removeIf(example->example.id==id); }
    public synchronized void clear() { examples.clear();nextId=1; }

    public synchronized Evaluation evaluate(double[] features, Gates gates) {
        double[] query=validate(features);
        if(gates==null) throw new IllegalArgumentException("Explicit external gates required");
        String blocked=gates.blockedReason();
        if(blocked!=null) return result(Recommendation.BLOCKED,blocked,0.5,1,Collections.emptyList());
        if(examples.isEmpty()) return result(Recommendation.ABSTAIN,"No labeled examples yet",0.5,1,Collections.emptyList());
        List<Example> sorted=new ArrayList<>(examples);
        sorted.sort(Comparator.comparingDouble((Example e)->distance(query,e.features)).thenComparingLong(e->e.id));
        double nearest=distance(query,sorted.get(0).features);
        // All exact matches participate in a consistency check, even beyond the top 3.
        Label exactLabel=null;boolean conflict=false;
        for(Example example:sorted) {
            if(distance(query,example.features)>1e-12) break;
            if(exactLabel!=null && exactLabel!=example.label) conflict=true;
            exactLabel=example.label;
        }
        int count=Math.min(NEIGHBORS,sorted.size());
        if(nearest<=1e-12) {
            count=0;for(Example example:sorted) {if(distance(query,example.features)>1e-12) break;count++;}
        }
        double totalWeight=0;for(int i=0;i<count;i++) totalWeight+=1/(0.05+distance(query,sorted.get(i).features));
        List<Neighbor> matches=new ArrayList<>();double vote=0;
        for(int i=0;i<count;i++) {
            Example e=sorted.get(i);double d=distance(query,e.features);
            Neighbor neighbor=new Neighbor(e,query,d,(1/(0.05+d))/totalWeight);matches.add(neighbor);vote+=neighbor.nudgeContribution;
        }
        double uncertainty=Math.min(1,Math.max(1-Math.abs(2*vote-1),nearest/MAX_DISTANCE));
        if(conflict) return result(Recommendation.ABSTAIN,"Conflicting labels for the exact same vector",vote,1,matches);
        if(nearest>MAX_DISTANCE) return result(Recommendation.ABSTAIN,"No nearby example; label this situation first",vote,uncertainty,matches);
        if(vote>ALLOW_THRESHOLD && vote<NUDGE_THRESHOLD) return result(Recommendation.ABSTAIN,"Nearby examples disagree; ask for a label",vote,uncertainty,matches);
        return result(vote>=NUDGE_THRESHOLD?Recommendation.NUDGE:Recommendation.ALLOW,
            nearest<=1e-12?"Exact saved label match":"Nearby saved examples agree",vote,uncertainty,matches);
    }
    private static Evaluation result(Recommendation recommendation,String reason,double vote,double uncertainty,List<Neighbor> neighbors) {
        return new Evaluation(recommendation,reason,vote,uncertainty,neighbors);
    }
    private static double distance(double[] query,double[] example) {
        double sum=0;for(int i=0;i<6;i++) {double delta=query[i]-example[i];sum+=delta*delta;}return Math.sqrt(sum/6);
    }
    private static double[] validate(double[] values) {
        if(values==null || values.length!=6) throw new IllegalArgumentException("Exactly six explicit features required");
        for(double value:values) if(!Double.isFinite(value)||value<0||value>1) throw new IllegalArgumentException("Finite features in [0,1] required");
        return values.clone();
    }
}
