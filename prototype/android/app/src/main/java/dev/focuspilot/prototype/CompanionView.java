package dev.focuspilot.prototype;

import android.content.Context;
import android.graphics.Canvas;
import android.graphics.Color;
import android.graphics.Paint;
import android.graphics.Path;
import android.graphics.RectF;
import android.os.SystemClock;
import android.view.View;

/** Original friendly goth companion; procedural native animation, no copied portraits. */
public final class CompanionView extends View {
    public enum State { IDLE, FOCUS, LISTEN, CELEBRATE, NUDGE, PAUSED }
    private final Paint paint=new Paint(Paint.ANTI_ALIAS_FLAG);
    private final Path shoulders=new Path(), fringe=new Path();
    private final RectF mouth=new RectF(190,143,210,159);
    private State state=State.IDLE;
    private boolean reduceMotion;
    private final Runnable nextFrame=() -> { if(canAnimate()) invalidate(); };
    public CompanionView(Context context) { super(context); setContentDescription("Friendly illustrated focus companion"); }
    public void setState(State state) { this.state=state; if(!canAnimate()) removeCallbacks(nextFrame); invalidate(); }
    public void setReduceMotion(boolean reduced) { reduceMotion=reduced; if(reduced) removeCallbacks(nextFrame); invalidate(); }
    private boolean canAnimate() { return !reduceMotion && state!=State.PAUSED && isShown() && getWindowVisibility()==VISIBLE; }
    private void color(int value) { paint.setColor(value); paint.setStyle(Paint.Style.FILL); }
    private void oval(Canvas canvas,float l,float t,float r,float b,int value) { color(value); canvas.drawOval(l,t,r,b,paint); }
    private void line(Canvas canvas,float x,float y,float xx,float yy,int value,float width) { color(value); paint.setStrokeWidth(width); paint.setStrokeCap(Paint.Cap.ROUND); canvas.drawLine(x,y,xx,yy,paint); }
    @Override protected void onDraw(Canvas canvas) {
        super.onDraw(canvas); float scale=Math.min(getWidth()/400f,getHeight()/280f);
        canvas.save(); canvas.translate((getWidth()-400*scale)/2,(getHeight()-280*scale)/2); canvas.scale(scale,scale);
        long time=SystemClock.uptimeMillis(); boolean animated=canAnimate(); float breath=animated ? (float)Math.sin(time/900.0)*2 : 0;
        float glow=animated ? (float)(Math.sin(time/500.0)+1)/2 : 0.5f;
        oval(canvas,72,33,328,267,Color.rgb(47,41,64));
        oval(canvas,108,231,292,252,Color.rgb(26,24,37));
        canvas.save(); canvas.translate(0,breath);
        int hair=Color.rgb(29,25,40), skin=Color.rgb(241,210,216), lilac=Color.rgb(203,171,238), ink=Color.rgb(49,35,60);
        oval(canvas,120,34,280,254,hair);
        shoulders.reset(); shoulders.moveTo(113,250); shoulders.cubicTo(122,194,153,198,200,192); shoulders.cubicTo(250,198,278,195,287,250); shoulders.close(); color(Color.rgb(113,87,143)); canvas.drawPath(shoulders,paint);
        oval(canvas,184,159,216,213,skin);
        oval(canvas,141,51,259,183,skin);
        oval(canvas,136,38,265,101,hair);
        fringe.reset(); fringe.moveTo(138,57); fringe.lineTo(168,116); fringe.lineTo(190,76); fringe.lineTo(205,103); fringe.lineTo(234,68); fringe.lineTo(260,93); fringe.lineTo(257,45); fringe.close(); color(hair); canvas.drawPath(fringe,paint);
        line(canvas,151,62,142,177,Color.rgb(82,64,106),5);
        line(canvas,252,65,261,180,Color.rgb(82,64,106),4);
        boolean blink=animated && time%4700<170;
        if(blink || state==State.PAUSED) { line(canvas,165,126,181,129,ink,3); line(canvas,221,129,237,126,ink,3); }
        else {
            oval(canvas,163,118,184,133,ink); oval(canvas,216,118,237,133,ink);
            oval(canvas,171,120,178,129,lilac); oval(canvas,222,120,229,129,lilac);
            oval(canvas,173,120,176,123,Color.WHITE); oval(canvas,224,120,227,123,Color.WHITE);
            line(canvas,162,118,156,114,ink,2); line(canvas,236,118,242,114,ink,2);
        }
        oval(canvas,154,139,177,146,Color.rgb(229,166,190)); oval(canvas,223,139,246,146,Color.rgb(229,166,190));
        color(ink); paint.setStyle(Paint.Style.STROKE); paint.setStrokeWidth(3);
        canvas.drawArc(mouth,12,156,false,paint); paint.setStyle(Paint.Style.FILL);
        line(canvas,183,186,217,186,ink,8); oval(canvas,196,183,204,191,lilac);
        oval(canvas,231,64,248,81,lilac); oval(canvas,236,61,251,74,hair);
        oval(canvas,144,150,152,160,lilac); oval(canvas,249,150,257,160,lilac);
        line(canvas,160,216,157,244,ink,3); line(canvas,240,216,243,244,ink,3);
        color(lilac); canvas.drawCircle(200,224,9,paint); color(Color.rgb(113,87,143)); canvas.drawCircle(204,221,8,paint);
        canvas.restore();
        if(state==State.LISTEN) { oval(canvas,312,76,350,114,Color.argb(120+(int)(glow*90),116,226,204)); line(canvas,331,86,331,100,ink,5); line(canvas,325,102,337,102,ink,2); }
        if(state==State.NUDGE) { oval(canvas,303,72,352,113,lilac); color(ink); paint.setTextSize(23); canvas.drawText("♡",315,101,paint); }
        if(state==State.CELEBRATE || state==State.FOCUS) {
            color(lilac); paint.setTextSize(28); canvas.drawText("✦",69,100+(animated?glow*6:0),paint); canvas.drawText("✧",305,182-(animated?glow*4:0),paint);
        }
        canvas.restore();
        removeCallbacks(nextFrame); if(animated) postDelayed(nextFrame,40);
    }
    @Override protected void onWindowVisibilityChanged(int visibility) { super.onWindowVisibilityChanged(visibility); removeCallbacks(nextFrame); if(visibility==VISIBLE) invalidate(); }
    @Override protected void onVisibilityChanged(View changedView,int visibility) { super.onVisibilityChanged(changedView,visibility); removeCallbacks(nextFrame); if(visibility==VISIBLE) invalidate(); }
    @Override protected void onDetachedFromWindow() { removeCallbacks(nextFrame); super.onDetachedFromWindow(); }
}
