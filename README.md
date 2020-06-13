# isobar

![ci](https://github.com/ideoforms/isobar/workflows/ci/badge.svg)

isobar is a Python library for creating and manipulating musical patterns, designed for use in algorithmic composition, generative music and sonification. It makes it quick and easy to express complex musical ideas, and can send and receive events from various different sources: MIDI, OSC, SocketIO, and .mid files.

The core element is a Timeline, which can control its own tempo or sync to an external clock. Onto this, you can schedule Patterns, which can be note sequences, control events, program changes, or other arbitrary events via lambda functions.

isobar includes a large array of basic compositional building blocks (see [Pattern Classes](#pattern-classes)), plus some advanced pattern generators for more sophisticated operations:

 - `PLSystem` can be used to generate patterns based on the branching grammars of [L-systems](http://en.wikipedia.org/wiki/L-system)
 - `PMarkov` generates first-order Markov chains, and can learn patterns from MIDI input via `MarkovLearner`
 - `PEuclidean` generates Euclidean rhythms
 - `PArpeggiator` supports various arpeggiator sequences
 - ..plus lots of pattern generators for chance operations are defined in [pattern/chance.py](isobar/pattern/chance.py)

# Usage

```python
import isobar as iso

#------------------------------------------------------------------------
# Create a geometric series on a minor scale.
# PingPong plays the series forward then backward. PLoop loops forever.
#------------------------------------------------------------------------
arpeggio = iso.PSeries(0, 2, 6)
arpeggio = iso.PDegree(arpeggio, iso.Scale.minor) + 72
arpeggio = iso.PPingPong(arpeggio)
arpeggio = iso.PLoop(arpeggio)

#------------------------------------------------------------------------
# Create a velocity sequence, with emphasis every 4th note,
# plus a random walk to create gradual dynamic changes.
# Amplitudes are in the MIDI velocity range (0..127).
#------------------------------------------------------------------------
amplitude = iso.PSequence([50, 35, 25, 35]) + iso.PBrown(0, 1, -20, 20)

#------------------------------------------------------------------------
# A Timeline schedules events at a specified tempo. By default, events
# are send to the system's default MIDI output.
#------------------------------------------------------------------------
timeline = iso.Timeline(120)

#------------------------------------------------------------------------
# Schedule events, with properties generated by the Pattern objects.
#------------------------------------------------------------------------
timeline.schedule({
    iso.EVENT_NOTE: arpeggio,
    iso.EVENT_DURATION: 0.25,
    iso.EVENT_AMPLITUDE: amplitude
})
```

## Examples

More examples are available in the [examples](examples) directory with this
distribution:

* [00.ex-hello-world.py](examples/00.ex-hello-world.py)
* [01.ex-basics.py](examples/01.ex-basics.py)
* [02.ex-subsequence.py](examples/02.ex-subsequence.py)
* [03.ex-euclidean.py](examples/03.ex-euclidean.py)
* [04.ex-permutations.py](examples/04.ex-permutations.py)
* [05.ex-piano-phase.py](examples/05.ex-piano-phase.py)
* [06.ex-walk.py](examples/06.ex-walk.py)
* [10.ex-lsystem-stochastic.py](examples/10.ex-lsystem-stochastic.py)
* [11.ex-lsystem-rhythm.py](examples/11.ex-lsystem-rhythm.py)
* [12.ex-lsystem-grapher.py](examples/12.ex-lsystem-grapher.py)
* [20.ex-midi-input.py](examples/20.ex-midi-input.py)
* [21.ex-midi-clock-sync.py](examples/21.ex-midi-clock-sync.py)
* [22.ex-midi-markov-learner.py](examples/22.ex-midi-markov-learner.py)
* [30.ex-midifile-read.py](examples/30.ex-midifile-read.py)
* [31.ex-midifile-write.py](examples/31.ex-midifile-write.py)
* [32.ex-midifile-markov.py](examples/32.ex-midifile-markov.py)

## Classes

Top-level classes: [Chord](isobar/chord.py), [Key](isobar/key.py), [Scale](isobar/scale.py), [Timeline](isobar/timeline.py), [Clock](isobar/clock.py)

I/O classes: [MIDI](isobar/io/midi), [MIDIFile](isobar/io/midifile), [OSC](isobar/io/osc), [SocketIO](isobar/io/socketio)

### Pattern classes:

    CORE (core.py)
    Pattern              - Abstract superclass of all pattern generators.
    PConstant            - Pattern returning a fixed value
    PRef                 - Pattern containing a reference to another pattern
    PFunc                - Returns the value generated by a function (taking no arguments).
    PArrayIndex          - Request a specified index from an array.
    PDict                - Construct a pattern from a dict of arrays, or an array of dicts.
    PDictKey             - Request a specified key from a dictionary.
    PConcatenate         - Concatenate the output of multiple sequences.
    PAbs                 - Absolute value of <input>
    PInt                 - Integer value of <input>
    PAdd                 - Add elements of two patterns (shorthand: patternA + patternB)
    PSub                 - Subtract elements of two patterns (shorthand: patternA - patternB)
    PMul                 - Multiply elements of two patterns (shorthand: patternA * patternB)
    PDiv                 - Divide elements of two patterns (shorthand: patternA / patternB)
    PFloorDiv            - Integer division (shorthand: patternA // patternB)
    PMod                 - Modulo elements of two patterns (shorthand: patternA % patternB)
    PPow                 - One pattern to the power of another (shorthand: patternA ** patternB)
    PLShift              - Binary left-shift (shorthand: patternA << patternB)
    PRShift              - Binary right-shift (shorthand: patternA << patternB)

    SCALAR (scalar.py)
    PChanged             - Outputs a 1 if the value of a pattern has changed.
    PDiff                - Outputs the difference between the current and previous values of an input pattern
    PNormalise           - Adaptively normalise <input> to [0..1] over a linear scale.
    PMap                 - Apply an arbitrary function to an input pattern.
    PMapEnumerated       - Apply arbitrary function to input, passing a counter.
    PLinLin              - Map <input> from linear range [a,b] to linear range [c,d].
    PLinExp              - Map <input> from linear range [a,b] to exponential range [c,d].
    PRound               - Round <input> to N decimal places.
    PScalar              - Reduce tuples and lists into single scalar values,
    PWrap                - Wrap input note values within <min>, <max>.
    PIndexOf             - Find index of items from <pattern> in <list>

    SEQUENCE (sequence.py)
    PSeries              - Arithmetic series, beginning at <start>, increment by <step>
    PRange               - Similar to PSeries, but specify a max/step value.
    PGeom                - Geometric series, beginning at <start>, multiplied by <step>
    PImpulse             - Outputs a 1 every <period> events, otherwise 0.
    PLoop                - Repeats a finite <pattern> for <n> repeats.
    PPingPong            - Ping-pong input pattern back and forth N times.
    PCreep               - Loop <length>-note segment, progressing <creep> notes after <count> repeats.
    PStutter             - Play each note of <pattern> <count> times.
    PSubsequence         - Returns a finite subsequence of an input pattern.
    PReverse             - Reverses a finite sequence.
    PReset               - Resets <pattern> each time it receives a zero-crossing from
    PCounter             - Increments a counter by 1 for each zero-crossing in <trigger>.
    PCollapse            - Skip over any rests in <input>
    PNoRepeats           - Skip over repeated values in <input>
    PPad                 - Pad <pattern> with rests until it reaches length <length>.
    PPadToMultiple       - Pad <pattern> with rests until its length is divisible by <multiple>.
    PArpeggiator         - Arpeggiator.
    PEuclidean           - Generate Euclidean rhythms.
    PPermut              - Generate every permutation of <count> input items.
    PDecisionPoint       - Each time its pattern is exhausted, requests a new pattern by calling <fn>.

    CHANCE (chance.py)
    PWhite               - White noise between <min> and <max>.
    PBrown               - Brownian noise, beginning at <value>, step +/-<step>.
    PWalk                - Random walk around list.
    PChoice              - Random selection from <values>
    PWeightedChoice      - Random selection from <values>, weighted by <weights>.
    PShuffle             - Shuffled list.
    PShuffleEvery        - Every <n> steps, take <n> values from <pattern> and reorder.
    PSkip                - Skip events with some probability, 1 - <play>.
    PFlipFlop            - flip a binary bit with some probability.
    PSwitchOne           - Capture <length> input values; repeat, switching two adjacent values <n> times.

    TONAL (tonal.py)
    PDegree              - Map scale index <degree> to MIDI notes in <scale>.
    PFilterByKey         - Filter notes based on their presence in <key>.
    PNearest             - Return nearest note in <key>.
    PMidiNoteToFrequency - Map MIDI note to frequency value.

    STATIC (static.py)
    PStaticGlobal        - Static global value identified by a string, with OSC listener.
    PStaticTimeline      - Returns the position (in beats) of the current timeline.

    FADE (fade.py)
    PFadeNotewise        - Fade a pattern in/out by introducing notes at a gradual rate.
    PFadeNotewiseRandom  - Fade a pattern in/out by gradually introducing random notes.

    MARKOV (markov.py)
    PMarkov              - First-order Markov chain generator.

    LSYSTEM (lsystem.py)
    PLSystem             - integer sequence derived from Lindenmayer systems

    WARP (warp.py)
    PWInterpolate        - Requests a new target warp value from <pattern> every <length> beats
    PWSine               - Sinosoidal warp, period <length> beats, amplitude +/-<amp>.
    PWRallantando        - Exponential deceleration to <amp> times the current tempo over <length> beats.

## Background

isobar was first designed for the generative sound installation [Variable 4](http://www.variable4.org.uk), in which it was used to generate musical structures in response to changing weather conditions. It was more recently used in [The Listening Machine](http://www.thelisteningmachine.org/), taking live input from Twitter and generating musical output from language patterns, streamed live over the internet.

Many of the concepts behind Pattern and its subclasses are inspired by the brilliant pattern library of the [SuperCollider](http://supercollider.sf.net) synthesis language.

