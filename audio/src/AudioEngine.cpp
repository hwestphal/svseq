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
    : mLink(link), mSampleRate(44100.), mOutputLatency(0), mSharedEngineData({0., false, false, 4., std::chrono::microseconds(0)}), mIsPlaying(false)
{
}

void AudioEngine::startPlaying()
{
    std::lock_guard<std::mutex> lock(mEngineDataGuard);
    mSharedEngineData.requestStart = true;
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

        engineData.events = mSharedEngineData.events;

        mEngineDataGuard.unlock();
    }

    return engineData;
}

void AudioEngine::createSunvoxEvents(const Link::SessionState sessionState,
                                     const double quantum,
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
        if (timeAtBeat >= maxTime)
        {
            break;
        }
        if (timeAtBeat >= beginHostTime && !events.empty())
        {
            sv_set_event_t(0, 1, beginTicks + round(((timeAtBeat - beginHostTime).count() * ticksPerSecond) / 1e6));
            for (auto const &e : events)
            {
                sv_send_event(0, std::get<0>(e), std::get<1>(e), std::get<2>(e), std::get<3>(e), std::get<4>(e), std::get<5>(e));
            }
        }
        beat += 1;
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
        createSunvoxEvents(sessionState, engineData.quantum, engineData.events, hostTime, ticks, numSamples);
    }
    sv_audio_callback(buffer, numSamples, 0, ticks);
}

} // namespace linkaudio
} // namespace ableton
