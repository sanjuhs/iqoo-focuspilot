package dev.focuspilot.prototype;

import java.util.ArrayList;
import java.util.Collections;
import java.util.List;

/** Manual few-shot labels for real complete snapshots. Separate from the synthetic sandbox. */
public final class LivePreferencePolicy {
    public static final int MAX_RECORDS=32,MIN_LABELS=3;
    public static final String PROVENANCE="REAL_OBSERVATION";
    public enum Label { ALLOW, NUDGE }
    public enum Recommendation { BLOCKED, ABSTAIN, ALLOW, NUDGE }
    private final List<Record> records=new ArrayList<>();
    private long nextId=1;

    public static final class Gates {
        public final boolean explicitlyEnabled,observationConsent,permission,activeFocus;
        public final long expectedObservationScopeId;
        public Gates(boolean enabled,boolean consent,boolean permission,boolean activeFocus,long expectedObservationScopeId) {
            explicitlyEnabled=enabled;observationConsent=consent;this.permission=permission;this.activeFocus=activeFocus;
            this.expectedObservationScopeId=expectedObservationScopeId;
        }
    }
    public static final class Record {
        public final long id,observedAtWall,observedAtElapsed,labeledAtElapsed;
        public final LivePreferenceScope scope;
        public final Label label;
        public final String provenance;
        private final double[] features;
        /** Strict restoration boundary; a record is not an attestation of OS event accuracy. */
        public Record(long id,LivePreferenceScope scope,double[] features,Label label,long observedAtWall,long observedAtElapsed,long labeledAtElapsed,String provenance) {
            if(id<1 || id==Long.MAX_VALUE || scope==null || scope.continuousLimitMs<=0 || scope.plannedFocusMs<=0 || label==null || observedAtWall<=0 || observedAtElapsed<0 ||
                labeledAtElapsed<observedAtElapsed || labeledAtElapsed-observedAtElapsed>ObservationSnapshot.MAX_AGE_MS || !PROVENANCE.equals(provenance))
                throw new IllegalArgumentException("Invalid real-observation preference record");
            this.id=id;this.scope=scope;this.features=validated(features);this.label=label;this.observedAtWall=observedAtWall;
            this.observedAtElapsed=observedAtElapsed;this.labeledAtElapsed=labeledAtElapsed;this.provenance=provenance;
        }
        public double[] features() { return features.clone(); }
    }
    public static final class Decision {
        public final Recommendation recommendation;
        public final String reason;
        /** A label vote and heuristic ambiguity index, never calibrated risk/confidence. */
        public final double nudgeVote,uncertainty;
        public final List<FewShotPolicy.Neighbor> neighbors;
        private Decision(Recommendation kind,String reason,double vote,double uncertainty,List<FewShotPolicy.Neighbor> neighbors) {
            recommendation=kind;this.reason=reason;nudgeVote=vote;this.uncertainty=uncertainty;
            this.neighbors=Collections.unmodifiableList(new ArrayList<>(neighbors));
        }
        public boolean canVetoHandSetNudge() { return recommendation==Recommendation.ALLOW; }
        /** Caller supplies its already validated budget/permission/focus/cooldown decision. */
        public boolean permitsHandSetNudge(boolean existingBudgetCooldownDecision) {
            return existingBudgetCooldownDecision && !canVetoHandSetNudge();
        }
    }
    public synchronized Record save(LivePreferenceScope scope,ObservationSnapshot snapshot,Label label,Gates gates,long nowElapsed) {
        String blocked=blocked(scope,snapshot,gates,nowElapsed);
        if(blocked!=null) throw new IllegalArgumentException("No label saved: "+blocked);
        Record record=new Record(nextId,scope,snapshot.features(),label,snapshot.observedAtWall,snapshot.observedAtElapsed,nowElapsed,PROVENANCE);
        nextId++;if(records.size()==MAX_RECORDS)records.remove(0);records.add(record);return record;
    }
    public synchronized List<Record> records() { return Collections.unmodifiableList(new ArrayList<>(records)); }
    public synchronized void clear() { records.clear();nextId=1; }
    public synchronized boolean delete(long id) { return records.removeIf(record->record.id==id); }
    /** All-or-nothing restore. Android store must also verify stored schema/mapping/fingerprint. */
    public synchronized void restore(List<Record> saved) {
        if(saved==null || saved.size()>MAX_RECORDS)throw new IllegalArgumentException("At most 32 real records required");
        List<Record> copy=new ArrayList<>();long maximum=0;
        for(Record record:saved) {
            if(record==null)throw new IllegalArgumentException("Null record");
            for(Record prior:copy)if(prior.id==record.id)throw new IllegalArgumentException("Duplicate record ID");
            copy.add(new Record(record.id,record.scope,record.features(),record.label,record.observedAtWall,record.observedAtElapsed,record.labeledAtElapsed,record.provenance));
            maximum=Math.max(maximum,record.id);
        }
        records.clear();records.addAll(copy);nextId=maximum+1;
    }
    public synchronized Decision evaluate(LivePreferenceScope scope,ObservationSnapshot snapshot,Gates gates,long nowElapsed) {
        String blocked=blocked(scope,snapshot,gates,nowElapsed);
        if(blocked!=null)return abstain(Recommendation.BLOCKED,blocked);
        List<FewShotPolicy.Example> scoped=new ArrayList<>();
        int distinct=0;
        for(Record record:records) {
            if(!record.scope.equals(scope))continue;
            boolean seen=false;
            for(FewShotPolicy.Example prior:scoped)if(java.util.Arrays.equals(prior.features(),record.features()))seen=true;
            if(!seen)distinct++;
            scoped.add(new FewShotPolicy.Example(record.id,record.features(),record.label==Label.NUDGE?FewShotPolicy.Label.NUDGE:FewShotPolicy.Label.ALLOW));
        }
        if(scoped.size()<MIN_LABELS || distinct<2)return abstain(Recommendation.ABSTAIN,"Need at least three labels across two distinct complete observations in this exact scope");
        FewShotPolicy retrieval=new FewShotPolicy();retrieval.restore(scoped);
        FewShotPolicy.Evaluation result=retrieval.evaluate(snapshot.features(),new FewShotPolicy.Gates(false,true,true,true,true,true));
        Recommendation kind=Recommendation.valueOf(result.recommendation.name());
        return new Decision(kind,result.reason,result.nudgeVote,result.uncertainty,result.neighbors);
    }
    private static Decision abstain(Recommendation kind,String reason) { return new Decision(kind,reason,0.5,1,Collections.emptyList()); }
    private static String blocked(LivePreferenceScope scope,ObservationSnapshot snapshot,Gates gates,long nowElapsed) {
        if(gates==null)return "Explicit eligibility gates missing";
        if(!gates.explicitlyEnabled)return "Live personalization disabled";
        if(!gates.observationConsent)return "Observation consent disabled";
        if(!gates.permission)return "Usage permission unavailable";
        if(!gates.activeFocus)return "Focus paused";
        if(scope==null || snapshot==null)return "No current scope or observation";
        if(snapshot.scopeId!=gates.expectedObservationScopeId)return "Observation belongs to an earlier focus/consent scope";
        if(!scope.matches(snapshot))return "Selected app or declared settings changed";
        if(nowElapsed<snapshot.observedAtElapsed || nowElapsed-snapshot.observedAtElapsed>ObservationSnapshot.MAX_AGE_MS)return "Observation stale";
        if(!snapshot.complete())return "Observation features missing: "+String.join("; ",snapshot.missingReasons());
        return null;
    }
    private static double[] validated(double[] features) {
        if(features==null || features.length!=6)throw new IllegalArgumentException("Six real features required");
        for(double value:features)if(!Double.isFinite(value)||value<0||value>1)throw new IllegalArgumentException("Complete finite features in [0,1] required");
        return features.clone();
    }
}
