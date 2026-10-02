package dev.focuspilot.prototype;

import org.junit.Test;
import static org.junit.Assert.assertEquals;

public final class CommandNumberWordsTest {
    private static void invalid(String... values) {
        for (String value : values) assertEquals("Rejected whole slot: " + value, -1, CommandNumberWords.parse(value));
    }

    @Test public void digitsAreBoundedByValueWithoutOverflow() {
        assertEquals(0, CommandNumberWords.parse("0"));
        assertEquals(7, CommandNumberWords.parse("007"));
        assertEquals(120, CommandNumberWords.parse("120"));
        assertEquals(999, CommandNumberWords.parse("999"));
        invalid("1000", "2147483648", "9999999999999999999999");
    }

    @Test public void basicEnglishNumbersAndCaseAreAccepted() {
        assertEquals(0, CommandNumberWords.parse("zero"));
        assertEquals(1, CommandNumberWords.parse("ONE"));
        assertEquals(8, CommandNumberWords.parse("eight"));
        assertEquals(11, CommandNumberWords.parse("eleven"));
        assertEquals(13, CommandNumberWords.parse("thirteen"));
        assertEquals(18, CommandNumberWords.parse("eighteen"));
        assertEquals(19, CommandNumberWords.parse("nineteen"));
        assertEquals(40, CommandNumberWords.parse("forty"));
        assertEquals(90, CommandNumberWords.parse("ninety"));
    }

    @Test public void tensCompoundAllowsSpacesOrOneCorrectWordHyphen() {
        assertEquals(25, CommandNumberWords.parse("twenty-five"));
        assertEquals(25, CommandNumberWords.parse("twenty five"));
        assertEquals(31, CommandNumberWords.parse("THIRTY-ONE"));
        assertEquals(99, CommandNumberWords.parse("  ninety   nine  "));
        invalid("twenty-zero", "twenty-ten", "twenty--five", "twenty - five", "one-hundred", "twenty-five-six");
    }

    @Test public void hundredsAllowOnlyOneThroughNineAndValidPositiveRemainder() {
        assertEquals(100, CommandNumberWords.parse("one hundred"));
        assertEquals(101, CommandNumberWords.parse("one hundred one"));
        assertEquals(219, CommandNumberWords.parse("two hundred nineteen"));
        assertEquals(350, CommandNumberWords.parse("three hundred fifty"));
        assertEquals(425, CommandNumberWords.parse("four hundred twenty-five"));
        assertEquals(999, CommandNumberWords.parse("nine hundred ninety nine"));
        invalid("hundred", "zero hundred", "ten hundred", "one hundred zero", "one hundred hundred", "one hundred one hundred", "nine hundred ninety ten");
    }

    @Test public void proseUnitsAndNumberSubstringsNeverPass() {
        invalid("about five", "five minutes", "start twenty five", "one two", "twenty thirty", "five five", "first", "a hundred", "three hundred fourty", "one hundred and one", "twenty and five");
    }

    @Test public void signsFractionsAndMixedRepresentationsAreRejected() {
        invalid("-5", "+5", "-five", "five-", "−5", "five point five", "5.5", "1/2", "½", "1e2", "1 hundred", "one hundred 5", "twenty 5", "2five", "0x20", "1,000");
    }

    @Test public void EmptyControlAndNonAsciiFormsAreRejected() {
        invalid(null, "", "   ", "five\n", "five\tfive", "\r5", "five\u2028five", "twenty–five", "５", "fivé", "five\u00a0");
    }
}
