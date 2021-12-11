/* Copyright 2016, Ableton AG, Berlin. All rights reserved.
 *
 *  This program is free software: you can redistribute it and/or modify
 *  it under the terms of the GNU General Public License as published by
 *  the Free Software Foundation, either version 2 of the License, or
 *  (at your option) any later version.
 *
 *  This program is distributed in the hope that it will be useful,
 *  but WITHOUT ANY WARRANTY; without even the implied warranty of
 *  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
 *  GNU General Public License for more details.
 *
 *  You should have received a copy of the GNU General Public License
 *  along with this program.  If not, see <http://www.gnu.org/licenses/>.
 *
 *  If you would like to incorporate Link into a proprietary software application,
 *  please contact <link-devs@ableton.com>.
 */

#include "AudioEngine.hpp"
#include <sunvox.h>

// Make sure to define this before <cmath> is included for Windows
#ifdef LINK_PLATFORM_WINDOWS
#define _USE_MATH_DEFINES
#endif
#include <cmath>

namespace ableton
{
namespace linkaudio
{

AudioEngine::AudioEngine(Link &link)
    : mLink(link)
    , mSampleRate(44100.)
    , mOutputLatency(0)
    , mSharedEngineData({0., false, false, 4., std::chrono::microseconds(0)})
    , mIsPlaying(false)
    , mTimeAtLastClick{}
{
}

void AudioEngine::startPlaying(bool metronome)
{
    std::lock_guard<std::mutex> lock(mEngineDataGuard);
    mSharedEngineData.requestStart = true;
    mSharedEngineData.metronome = metronome;
}

void AudioEngine::stopPlaying()
{
    std::lock_guard<std::mutex> lock(mEngineDataGuard);
    mSharedEngineData.requestStop = true;
}

void AudioEngine::setTempo(double tempo)
{
    std::lock_guard<std::mutex> lock(mEngineDataGuard);
    mSharedEngineData.requestedTempo = tempo;
}

double AudioEngine::quantum() const
{
    return mSharedEngineData.quantum;
}

void AudioEngine::setQuantum(double quantum)
{
    std::lock_guard<std::mutex> lock(mEngineDataGuard);
    mSharedEngineData.quantum = quantum;
}

std::chrono::microseconds AudioEngine::latency() const
{
    return mSharedEngineData.latency;
}

void AudioEngine::setLatency(std::chrono::microseconds latency)
{
    std::lock_guard<std::mutex> lock(mEngineDataGuard);
    mSharedEngineData.latency = latency;
}

double AudioEngine::swing() const
{
    return mSharedEngineData.swing;
}

void AudioEngine::setSwing(double swing)
{
    std::lock_guard<std::mutex> lock(mEngineDataGuard);
    mSharedEngineData.swing = swing;
}

void AudioEngine::setEvents(std::vector<std::tuple<int, int, int, int, int, int>> &events)
{
    std::lock_guard<std::mutex> lock(mEngineDataGuard);
    mSharedEngineData.events = events;
}

void AudioEngine::setBufferSize(unsigned long size)
{
    mBufferSize = size;
}

void AudioEngine::setSampleRate(double sampleRate)
{
    mSampleRate = sampleRate;
}

AudioEngine::EngineData AudioEngine::pullEngineData()
{
    auto engineData = EngineData{};
    if (mEngineDataGuard.try_lock())
    {
        engineData.requestedTempo = mSharedEngineData.requestedTempo;
        mSharedEngineData.requestedTempo = 0;

        engineData.requestStart = mSharedEngineData.requestStart;
        mSharedEngineData.requestStart = false;

        engineData.requestStop = mSharedEngineData.requestStop;
        mSharedEngineData.requestStop = false;

        engineData.quantum = mSharedEngineData.quantum;

        engineData.latency = mSharedEngineData.latency;

        engineData.swing = mSharedEngineData.swing;

        engineData.events = mSharedEngineData.events;

        engineData.metronome = mSharedEngineData.metronome;

        mEngineDataGuard.unlock();
    }

    return engineData;
}

void AudioEngine::createSunvoxEvents(const Link::SessionState sessionState,
                                     const double quantum,
                                     const double swing,
                                     const std::vector<std::tuple<int, int, int, int, int, int>> &events,
                                     const std::chrono::microseconds beginHostTime,
                                     const uint32_t beginTicks,
                                     const std::size_t numSamples)
{
    using namespace std::chrono;

    const auto microsPerSample = 1e6 / mSampleRate;
    const auto ticksPerSecond = sv_get_ticks_per_second();
    const auto maxTime = beginHostTime + microseconds(llround(numSamples * microsPerSample));

    long long beat = std::max(0., sessionState.beatAtTime(beginHostTime, quantum) * 4.);
    for (;;)
    {
        const auto timeAtBeat = sessionState.timeAtBeat(beat / 4., quantum);
        const auto swingTimeAtBeat = (beat % 2) == 1 ? sessionState.timeAtBeat((beat + swing) / 4., quantum) : timeAtBeat;

        if (timeAtBeat >= maxTime)
        {
            break;
        }

        if (timeAtBeat >= beginHostTime && !events.empty())
        {
            const auto timeAtBeat_1_32 = sessionState.timeAtBeat((beat + .5) / 4., quantum);
            const auto timeAtBeat_1_24 = sessionState.timeAtBeat((beat + 2./3.) / 4., quantum);
            const auto timeAtBeat_2_24 = sessionState.timeAtBeat((beat + 4./3.) / 4., quantum);

            sv_lock_slot(0);

            sv_set_event_t(0, 1, beginTicks + uint32_t(round(((swingTimeAtBeat - beginHostTime).count() * ticksPerSecond) / 1e6)));
            for (auto const &e : events)
            {
                sv_send_event(0, std::get<0>(e), std::get<1>(e) & 0xff, std::get<2>(e), std::get<3>(e), std::get<4>(e), std::get<5>(e));
            }

            sv_set_event_t(0, 1, beginTicks + uint32_t(round(((timeAtBeat_1_32 - beginHostTime).count() * ticksPerSecond) / 1e6)));
            for (auto const &e : events)
            {
                const auto tone = std::get<1>(e) & 0xff;
                const auto trigger = std::get<1>(e) >> 8;
                if (trigger == 1 && tone > 0 && tone < 128) {
                    sv_send_event(0, std::get<0>(e), tone, std::get<2>(e), std::get<3>(e), 0, 0);
                }
            }

            sv_set_event_t(0, 1, beginTicks + uint32_t(round(((timeAtBeat_1_24 - beginHostTime).count() * ticksPerSecond) / 1e6)));
            for (auto const &e : events)
            {
                const auto tone = std::get<1>(e) & 0xff;
                const auto trigger = std::get<1>(e) >> 8;
                if (trigger == 2 && tone > 0 && tone < 128) {
                    sv_send_event(0, std::get<0>(e), tone, std::get<2>(e), std::get<3>(e), 0, 0);
                }
            }

            sv_set_event_t(0, 1, beginTicks + uint32_t(round(((timeAtBeat_2_24 - beginHostTime).count() * ticksPerSecond) / 1e6)));
            for (auto const &e : events)
            {
                const auto tone = std::get<1>(e) & 0xff;
                const auto trigger = std::get<1>(e) >> 8;
                if (trigger == 2 && tone > 0 && tone < 128) {
                    sv_send_event(0, std::get<0>(e), tone, std::get<2>(e), std::get<3>(e), 0, 0);
                }
            }

            sv_set_event_t(0, 0, 0);
            sv_unlock_slot(0);
        }
        beat += 1;
    }
}


void AudioEngine::renderMetronomeIntoBuffer(const Link::SessionState sessionState,
  const double quantum,
  const std::chrono::microseconds beginHostTime,
  float *buffer,
  const std::size_t numSamples)
{
  using namespace std::chrono;

  // Metronome frequencies
  static const double highTone = 1567.98;
  static const double lowTone = 1108.73;
  // 100ms click duration
  static const auto clickDuration = duration<double>{0.1};

  // The number of microseconds that elapse between samples
  const auto microsPerSample = 1e6 / mSampleRate;

  for (std::size_t i = 0; i < numSamples; ++i)
  {
    double amplitude = 0.;
    // Compute the host time for this sample and the last.
    const auto hostTime = beginHostTime + microseconds(llround(static_cast<double>(i) * microsPerSample));
    const auto lastSampleHostTime = hostTime - microseconds(llround(microsPerSample));

    // Only make sound for positive beat magnitudes. Negative beat
    // magnitudes are count-in beats.
    if (sessionState.beatAtTime(hostTime, quantum) >= 0.)
    {
      // If the phase wraps around between the last sample and the
      // current one with respect to a 1 beat quantum, then a click
      // should occur.
      if (sessionState.phaseAtTime(hostTime, 1)
          < sessionState.phaseAtTime(lastSampleHostTime, 1))
      {
        mTimeAtLastClick = hostTime;
      }

      const auto secondsAfterClick =
        duration_cast<duration<double>>(hostTime - mTimeAtLastClick);

      // If we're within the click duration of the last beat, render
      // the click tone into this sample
      if (secondsAfterClick < clickDuration)
      {
        // If the phase of the last beat with respect to the current
        // quantum was zero, then it was at a quantum boundary and we
        // want to use the high tone. For other beats within the
        // quantum, use the low tone.
        const auto freq =
          floor(sessionState.phaseAtTime(hostTime, quantum)) == 0 ? highTone : lowTone;

        // Simple cosine synth
        amplitude = cos(2 * M_PI * secondsAfterClick.count() * freq)
                    * (1 - sin(5 * M_PI * secondsAfterClick.count()));
      }
    }
    buffer[2 * i] += amplitude;
    buffer[2 * i + 1] += amplitude;
  }
}


void AudioEngine::audioCallback(
    const std::chrono::microseconds time, const std::size_t numSamples, float *buffer)
{
    const auto engineData = pullEngineData();

    const auto hostTime = time + engineData.latency;

    auto sessionState = mLink.captureAudioSessionState();

    if (engineData.requestStart)
    {
        sessionState.setIsPlaying(true, hostTime);
    }

    if (engineData.requestStop)
    {
        sessionState.setIsPlaying(false, hostTime);
    }

    if (!mIsPlaying && sessionState.isPlaying())
    {
        // Reset the timeline so that beat 0 corresponds to the time when transport starts
        sessionState.requestBeatAtStartPlayingTime(0, engineData.quantum);
        mIsPlaying = true;
    }
    else if (mIsPlaying && !sessionState.isPlaying())
    {
        mIsPlaying = false;
    }

    if (engineData.requestedTempo > 0)
    {
        // Set the newly requested tempo from the beginning of this buffer
        sessionState.setTempo(engineData.requestedTempo, hostTime);
    }

    // Timeline modifications are complete, commit the results
    mLink.commitAudioSessionState(sessionState);

    const uint32_t ticks = sv_get_ticks();
    if (mIsPlaying)
    {
        // As long as the engine is playing, generate sunvox events at the appropriate beats.
        createSunvoxEvents(sessionState, engineData.quantum, engineData.swing, engineData.events, hostTime, ticks, numSamples);
    }
    sv_audio_callback(buffer, numSamples, 0, ticks);

    if (mIsPlaying && engineData.metronome)
    {
        renderMetronomeIntoBuffer(sessionState, engineData.quantum, hostTime, buffer, numSamples);
    }
}

} // namespace linkaudio
} // namespace ableton
