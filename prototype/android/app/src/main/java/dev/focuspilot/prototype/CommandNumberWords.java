package dev.focuspilot.prototype;

import java.util.ArrayList;
import java.util.List;
import java.util.Locale;

/** Exact English integer slots only; this utility does not search or interpret prose. */
public final class CommandNumberWords {
    private static final String[] SMALL = {
        "zero", "one", "two", "three", "four", "five", "six", "seven", "eight", "nine",
        "ten", "eleven", "twelve", "thirteen", "fourteen", "fifteen", "sixteen", "seventeen",
        "eighteen", "nineteen"
    };
    private static final String[] TENS = {
        "twenty", "thirty", "forty", "fifty", "sixty", "seventy", "eighty", "ninety"
    };

    private CommandNumberWords() {}

    /**
     * Returns an integer from zero through 999, or -1 for an invalid whole slot.
     * Ordinary spaces and ASCII letter case may vary. Hyphens only join a tens
     * word to a one-through-nine word. Digits cannot mix with words; "and" is
     * deliberately unsupported so compound-command handling remains independent.
     */
    public static int parse(String input) {
        if (input == null || input.isEmpty()) return -1;
        // Do not trim away signs, controls, line breaks or non-English characters.
        for (int i = 0; i < input.length(); i++) {
            char c = input.charAt(i);
            if (!(c >= 'a' && c <= 'z') && !(c >= 'A' && c <= 'Z') &&
                !(c >= '0' && c <= '9') && c != ' ' && c != '-') return -1;
        }
        String text = input.trim().toLowerCase(Locale.ROOT);
        if (text.isEmpty()) return -1;
        boolean hasDigit = false;
        for (int i = 0; i < text.length(); i++) {
            char c = text.charAt(i);
            if (c >= '0' && c <= '9') hasDigit = true;
        }
        if (hasDigit) {
            int value = 0;
            for (int i = 0; i < text.length(); i++) {
                char c = text.charAt(i);
                if (c < '0' || c > '9') return -1;
                value = value * 10 + c - '0';
                if (value > 999) return -1;
            }
            return value;
        }

        List<String> words = new ArrayList<>(4);
        for (String token : text.split(" +")) {
            if (token.indexOf('-') >= 0) {
                String[] pair = token.split("-", -1);
                if (pair.length != 2 || tens(pair[0]) < 20 || small(pair[1]) < 1 || small(pair[1]) > 9)
                    return -1;
                words.add(pair[0]);
                words.add(pair[1]);
            } else {
                words.add(token);
            }
            if (words.size() > 4) return -1;
        }
        if (words.size() >= 2 && words.get(1).equals("hundred")) {
            int hundreds = small(words.get(0));
            if (hundreds < 1 || hundreds > 9) return -1;
            if (words.size() == 2) return hundreds * 100;
            int remainder = belowHundred(words.subList(2, words.size()));
            return remainder > 0 ? hundreds * 100 + remainder : -1;
        }
        return belowHundred(words);
    }

    private static int belowHundred(List<String> words) {
        if (words.size() == 1) {
            int value = small(words.get(0));
            return value >= 0 ? value : tens(words.get(0));
        }
        if (words.size() == 2) {
            int tens = tens(words.get(0));
            int ones = small(words.get(1));
            return tens >= 20 && ones >= 1 && ones <= 9 ? tens + ones : -1;
        }
        return -1;
    }

    private static int small(String word) {
        for (int i = 0; i < SMALL.length; i++) if (SMALL[i].equals(word)) return i;
        return -1;
    }

    private static int tens(String word) {
        for (int i = 0; i < TENS.length; i++) if (TENS[i].equals(word)) return (i + 2) * 10;
        return -1;
    }
}
