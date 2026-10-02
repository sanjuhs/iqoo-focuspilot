package dev.focuspilot.prototype;
import org.junit.Test;
import static org.junit.Assert.*;

public class CoreTest {
    @Test public void policyIsMonotonicAndRespectsPauseCooldown() {
        DecisionPolicy policy = new DecisionPolicy(); double previous = -1;
        for (long used = 0; used < 250_000; used += 1000) {
            DecisionPolicy.Result result = policy.evaluate(used, 60_000, true, 100_000, -1);
            assertTrue(result.score >= previous); previous = result.score;
        }
        assertFalse(policy.evaluate(60_000, 60_000, true, 0, -1).nudge);
        assertFalse(policy.evaluate(120_000, 60_000, false, 100_000, -1).nudge);
        assertFalse(policy.evaluate(120_000, 60_000, true, 100_000, 90_000).nudge);
        assertTrue(policy.evaluate(120_000, 60_000, true, 150_000, 90_000).nudge);
    }
    @Test public void pausedSessionDoesNotGrowAndResumeIsIdempotent() {
        FocusSession session = new FocusSession(); session.start(1000); session.start(2000);
        session.pause(5000); assertEquals(4000, session.elapsed(9000));
        session.start(10_000); assertEquals(5000, session.elapsed(11_000));
        session.pause(11_000); session.pause(20_000); assertEquals(5000, session.elapsed(30_000));
    }
    @Test public void virtualPenaltyIsBoundedAndCannotDuplicateWithinCooldown() {
        VirtualLedger ledger = new VirtualLedger(); DecisionPolicy policy = new DecisionPolicy();
        DecisionPolicy.Result nudge = policy.evaluate(120_000, 60_000, true, 0, -1);
        assertTrue(ledger.apply(nudge, 0)); assertEquals(95, ledger.points());
        assertFalse(ledger.apply(nudge, 10)); assertEquals(95, ledger.points());
        for (int i = 1; i < 40; i++) ledger.apply(nudge, i * 60_000L);
        assertEquals(0, ledger.points());
    }
    @Test public void parserValidatesBoundsAndAbstainsOnExtraInstructions() {
        CommandParser parser = new CommandParser();
        assertEquals(CommandParser.Kind.START, parser.parse("start focus").kind);
        assertEquals(CommandParser.Kind.PAUSE, parser.parse("pause").kind);
        assertEquals(0, parser.parse("set an alarm at 12 am").hour);
        assertEquals(19, parser.parse("alarm 7:30 pm").hour);
        assertEquals(CommandParser.Kind.UNKNOWN, parser.parse("alarm 24:00").kind);
        assertEquals(CommandParser.Kind.UNKNOWN, parser.parse("alarm 7:99").kind);
        assertEquals(CommandParser.Kind.UNKNOWN, parser.parse("alarm 0 am").kind);
        assertEquals(CommandParser.Kind.UNKNOWN, parser.parse("alarm 7:30 then transfer money").kind);
    }
}
