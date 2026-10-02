package dev.focuspilot.prototype;

import android.app.Activity;
import android.os.Build;
import android.os.Bundle;
import android.graphics.Color;
import android.graphics.Insets;
import android.graphics.Typeface;
import android.text.InputType;
import android.view.Gravity;
import android.view.WindowInsets;
import android.view.WindowManager;
import android.view.inputmethod.EditorInfo;
import android.view.inputmethod.InputMethodManager;
import android.widget.Button;
import android.widget.EditText;
import android.widget.LinearLayout;
import android.widget.ScrollView;
import android.widget.Switch;
import android.widget.TextView;
import java.util.Locale;

/** Explicit synthetic developer sandbox, with no phone observation or action execution. */
public final class PolicyLabActivity extends Activity {
    private static final int BACKGROUND = Color.rgb(26, 26, 36);
    private static final int SURFACE = Color.rgb(42, 40, 56);
    private static final int TEXT = Color.rgb(244, 239, 250);
    private static final int MUTED = Color.rgb(192, 181, 207);
    private static final int LILAC = Color.rgb(201, 183, 234);
    private static final int TEAL = Color.rgb(121, 219, 200);
    private static final double[] DEFAULTS = {0.7, 0.6, 0.4, 0.8, 0.2, 0.5};
    private static final String[] LABELS = {"Selected-app budget overrun", "Continuous-session overrun",
        "Reopen count", "Active-focus overlap", "Deferred nudges", "Elapsed-time overrun"};

    private final EditText[] inputs = new EditText[6];
    private Switch paused, consent;
    private TextView result, contributionDetails, ablationDetails;

    @Override public void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        getWindow().setStatusBarColor(BACKGROUND);
        getWindow().setNavigationBarColor(BACKGROUND);
        getWindow().setSoftInputMode(WindowManager.LayoutParams.SOFT_INPUT_ADJUST_RESIZE);
        getWindow().getDecorView().setSystemUiVisibility(0);

        LinearLayout frame = new LinearLayout(this);
        frame.setOrientation(LinearLayout.VERTICAL);
        frame.setBackgroundColor(BACKGROUND);
        frame.setPadding(dp(16), dp(16), dp(16), dp(16));
        frame.setOnApplyWindowInsetsListener((view, insets) -> {
            if (Build.VERSION.SDK_INT >= 30) {
                Insets bars = insets.getInsets(WindowInsets.Type.systemBars() | WindowInsets.Type.displayCutout());
                view.setPadding(bars.left + dp(16), bars.top + dp(12), bars.right + dp(16), bars.bottom + dp(12));
            } else {
                view.setPadding(insets.getSystemWindowInsetLeft() + dp(16),
                    insets.getSystemWindowInsetTop() + dp(12),
                    insets.getSystemWindowInsetRight() + dp(16),
                    insets.getSystemWindowInsetBottom() + dp(12));
            }
            return insets;
        });

        ScrollView scroll = new ScrollView(this);
        scroll.setFillViewport(true);
        LinearLayout content = new LinearLayout(this);
        content.setOrientation(LinearLayout.VERTICAL);
        content.setPadding(0, 0, 0, dp(16));
        scroll.addView(content, new ScrollView.LayoutParams(-1, -2));
        frame.addView(scroll, new LinearLayout.LayoutParams(-1, -1));
        setContentView(frame);
        frame.requestApplyInsets();

        Button back = button("Back to FocusPilot");
        back.setOnClickListener(view -> finish());
        content.addView(back);
        text(content, "Decision lab", 28, LILAC, true);
        text(content, "A small network, visible reasons", 17, TEAL, false);
        text(content, "Developer sandbox · pre-event research\n65 trained parameters · standard Java CPU\n"
            + "All six values below are invented inputs. Nothing here observes your phone, moves money, "
            + "or explains a language model.", 15, MUTED, false);

        LinearLayout featureCard = card(content);
        text(featureCard, "Your synthetic vector", 20, TEXT, true);
        text(featureCard, "Edit any value from 0 to 1. These normalized features have no calibrated real-world units. "
            + "Missing phone observations are never replaced with guessed values.", 14, MUTED, false);
        String[] restored = savedInstanceState == null ? null : savedInstanceState.getStringArray("features");
        for (int i = 0; i < inputs.length; i++) {
            text(featureCard, (i + 1) + ". " + LABELS[i], 15, TEXT, true);
            EditText input = new EditText(this);
            input.setSingleLine(true);
            input.setTextColor(TEXT);
            input.setHintTextColor(MUTED);
            input.setTextSize(17);
            input.setInputType(InputType.TYPE_CLASS_NUMBER | InputType.TYPE_NUMBER_FLAG_DECIMAL | InputType.TYPE_NUMBER_FLAG_SIGNED);
            input.setImeOptions(EditorInfo.IME_ACTION_DONE);
            input.setContentDescription(LABELS[i] + ", explicit synthetic value between zero and one");
            input.setText(restored != null && restored.length == 6 ? restored[i] : Double.toString(DEFAULTS[i]));
            input.setMinHeight(dp(52));
            featureCard.addView(input, new LinearLayout.LayoutParams(-1, -2));
            inputs[i] = input;
        }

        LinearLayout gateCard = card(content);
        text(gateCard, "External gates", 20, TEXT, true);
        text(gateCard, "These are simulated policy controls, separate from the network and Android permissions. "
            + "A paused or no-consent state blocks a recommendation regardless of score. Manual sandbox inspection remains available.", 14, MUTED, false);
        paused = toggle("Sandbox paused", savedInstanceState != null && savedInstanceState.getBoolean("paused"));
        consent = toggle("Sandbox consent enabled", savedInstanceState != null && savedInstanceState.getBoolean("consent"));
        gateCard.addView(paused);
        gateCard.addView(consent);

        Button inspect = button("Inspect this vector");
        inspect.setOnClickListener(view -> {
            refresh();
            InputMethodManager keyboard = (InputMethodManager) getSystemService(INPUT_METHOD_SERVICE);
            if (keyboard != null) keyboard.hideSoftInputFromWindow(inspect.getWindowToken(), 0);
        });
        content.addView(inspect);
        paused.setOnCheckedChangeListener((buttonView, isChecked) -> refresh());
        consent.setOnCheckedChangeListener((buttonView, isChecked) -> refresh());

        LinearLayout resultCard = card(content);
        result = text(resultCard, "", 16, TEXT, false);
        LinearLayout hiddenCard = card(content);
        text(hiddenCard, "Eight hidden units", 20, LILAC, true);
        text(hiddenCard, "Each contribution is exact before the sigmoid. Bias + all contributions = logit. "
            + "Clamping a unit to zero is a controlled intervention inside this tiny model; units have no validated concept names.", 14, MUTED, false);
        contributionDetails = text(hiddenCard, "", 14, TEXT, false);
        contributionDetails.setTypeface(Typeface.MONOSPACE);
        contributionDetails.setTextIsSelectable(true);

        LinearLayout ablationCard = card(content);
        text(ablationCard, "What if one feature were zero?", 20, LILAC, true);
        text(ablationCard, "Each row recomputes the whole network with one synthetic input set to zero. "
            + "Ablation changes do not generally add up and are not conclusions about people.", 14, MUTED, false);
        ablationDetails = text(ablationCard, "", 14, TEXT, false);
        ablationDetails.setTextIsSelectable(true);

        LinearLayout provenance = card(content);
        text(provenance, "Training provenance", 20, TEXT, true);
        text(provenance, "6 → 8 ReLU → 1 sigmoid\nNonnegative weights; signed biases\n"
            + "Seed " + TrainedPolicy.TRAINING_SEED + " · selected epoch " + TrainedPolicy.SELECTED_EPOCH
            + "\nTrain/dev/holdout: 640 / 320 / 480 synthetic scenarios\n"
            + "Synthetic holdout: 472 / 480 correct (98.33%)\n"
            + "All labels came from one known invented teacher. This measures imitation of that rule, not real productivity learning. "
            + "The exact teacher scores 100% by construction. The app's existing hand-set focus monitor remains separate.", 14, MUTED, false);
        TextView hashes = text(provenance, "Python source SHA-256\n" + TrainedPolicy.SOURCE_SHA256
            + "\n\nParameters SHA-256\n" + TrainedPolicy.PARAMETERS_SHA256, 12, MUTED, false);
        hashes.setTypeface(Typeface.MONOSPACE);
        hashes.setTextIsSelectable(true);
        refresh();
    }

    @Override protected void onSaveInstanceState(Bundle state) {
        super.onSaveInstanceState(state);
        String[] values = new String[6];
        for (int i = 0; i < inputs.length; i++) values[i] = inputs[i].getText().toString();
        state.putStringArray("features", values);
        state.putBoolean("paused", paused.isChecked());
        state.putBoolean("consent", consent.isChecked());
    }

    private void refresh() {
        if (result == null) return;
        double[] values = new double[6];
        for (int i = 0; i < inputs.length; i++) {
            inputs[i].setError(null);
            try {
                values[i] = Double.parseDouble(inputs[i].getText().toString().trim());
                if (!Double.isFinite(values[i]) || values[i] < 0.0 || values[i] > 1.0)
                    throw new NumberFormatException("outside range");
            } catch (NumberFormatException error) {
                inputs[i].setError("Use a finite number from 0 to 1");
                result.setText("No evaluation: check synthetic feature " + (i + 1) + ".");
                contributionDetails.setText("");
                ablationDetails.setText("");
                return;
            }
        }
        TrainedPolicy.Evaluation evaluation = TrainedPolicy.evaluate(values);
        String gate;
        if (paused.isChecked()) gate = "BLOCKED: sandbox paused";
        else if (!consent.isChecked()) gate = "BLOCKED: sandbox consent disabled";
        else gate = evaluation.score >= TrainedPolicy.DEV_THRESHOLD ? "Offer a sandbox nudge" : "Allow in the sandbox";
        result.setText(String.format(Locale.US,
            "Synthetic score: %.8f\nLogit: %.8f\nDev-selected threshold: %.2f\n\n%s\n"
            + "No action is executed. Focus/cooldown/freshness checks belong outside this evaluator.",
            evaluation.score, evaluation.logit, TrainedPolicy.DEV_THRESHOLD, gate));

        StringBuilder hidden = new StringBuilder();
        hidden.append(String.format(Locale.US, "Output bias: %+.8f\n\n", evaluation.outputBias));
        double[] pre = evaluation.hiddenPreactivations();
        double[] activations = evaluation.hiddenActivations();
        double[] contributions = evaluation.hiddenContributions();
        double[] suppressed = evaluation.suppressedHiddenScores();
        for (int j = 0; j < 8; j++) {
            hidden.append(String.format(Locale.US,
                "Unit %d\n pre %.6g · ReLU %.6g\n logit contribution %+.8f\n clamp score %.8f · drop %.6g\n\n",
                j, pre[j], activations[j], contributions[j], suppressed[j], evaluation.score - suppressed[j]));
        }
        contributionDetails.setText(hidden.toString().trim());

        StringBuilder ablation = new StringBuilder();
        double[] scores = evaluation.featureAblationScores();
        double[] drops = evaluation.featureAblationDrops();
        for (int i = 0; i < 6; i++) {
            ablation.append(String.format(Locale.US, "%s\n %.4f → 0\n Score %.8f · drop %.6g\n\n",
                LABELS[i], values[i], scores[i], drops[i]));
        }
        ablationDetails.setText(ablation.toString().trim());
    }

    private Switch toggle(String label, boolean checked) {
        Switch view = new Switch(this);
        view.setText(label);
        view.setTextColor(TEXT);
        view.setTextSize(15);
        view.setMinHeight(dp(52));
        view.setChecked(checked);
        view.setPadding(0, dp(4), 0, dp(4));
        return view;
    }

    private LinearLayout card(LinearLayout parent) {
        LinearLayout view = new LinearLayout(this);
        view.setOrientation(LinearLayout.VERTICAL);
        view.setBackgroundColor(SURFACE);
        view.setPadding(dp(16), dp(12), dp(16), dp(12));
        LinearLayout.LayoutParams params = new LinearLayout.LayoutParams(-1, -2);
        params.setMargins(0, dp(14), 0, 0);
        parent.addView(view, params);
        return view;
    }

    private TextView text(LinearLayout parent, String value, int size, int color, boolean bold) {
        TextView view = new TextView(this);
        view.setText(value);
        view.setTextSize(size);
        view.setTextColor(color);
        view.setPadding(0, dp(5), 0, dp(7));
        if (bold) view.setTypeface(Typeface.DEFAULT, Typeface.BOLD);
        parent.addView(view, new LinearLayout.LayoutParams(-1, -2));
        return view;
    }

    private Button button(String value) {
        Button view = new Button(this);
        view.setText(value);
        view.setAllCaps(false);
        view.setTextColor(BACKGROUND);
        view.setBackgroundTintList(android.content.res.ColorStateList.valueOf(LILAC));
        view.setMinHeight(dp(52));
        view.setGravity(Gravity.CENTER);
        return view;
    }

    private int dp(int value) { return Math.round(value * getResources().getDisplayMetrics().density); }
}
