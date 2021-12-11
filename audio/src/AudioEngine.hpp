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

#pragma once

// Make sure to define this before <cmath> is included for Windows
#define _USE_MATH_DEFINES
#include <ableton/Link.hpp>
#include <mutex>

namespace ableton
{
namespace linkaudio
{

class AudioEngine
{
public:
    AudioEngine(Link &link);
    void startPlaying(bool metronome);
    void stopPlaying();
    void setTempo(double tempo);
    double quantum() const;
    void setQuantum(double quantum);
    std::chrono::microseconds latency() const;
    void setLatency(std::chrono::microseconds latency);
    double swing() const;
    void setSwing(double swing);
    void setEvents(std::vector<std::tuple<int, int, int, int, int, int>> &events);

private:
    struct EngineData
    {
        double requestedTempo;
        bool requestStart;
        bool requestStop;
        double quantum;
        std::chrono::microseconds latency;
        double swing;
        std::vector<std::tuple<int, int, int, int, int, int>> events;
        bool metronome;
    };

    void setBufferSize(unsigned long size);
    void setSampleRate(double sampleRate);
    EngineData pullEngineData();
    void audioCallback(std::chrono::microseconds hostTime,
                       std::size_t numSamples,
                       float *buffer);
    void createSunvoxEvents(Link::SessionState sessionState,
                            double quantum,
                            double swing,
                            const std::vector<std::tuple<int, int, int, int, int, int>> &events,
                            std::chrono::microseconds beginHostTime,
                            uint32_t beginTicks,
                            std::size_t numSamples);
    void renderMetronomeIntoBuffer(Link::SessionState sessionState,
                                   double quantum,
                                   std::chrono::microseconds beginHostTime,
                                   float *buffer,
                                   std::size_t numSamples);

    Link &mLink;
    double mSampleRate;
    std::chrono::microseconds mOutputLatency;
    unsigned long mBufferSize;
    EngineData mSharedEngineData;
    bool mIsPlaying;
    std::mutex mEngineDataGuard;
    std::chrono::microseconds mTimeAtLastClick;

    friend class AudioPlatform;
};

} // namespace linkaudio
} // namespace ableton
