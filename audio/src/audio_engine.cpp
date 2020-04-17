#include "AudioPlatform.hpp"
#include <pybind11/pybind11.h>
#include <pybind11/functional.h>
#include <pybind11/chrono.h>

#define SUNVOX_MAIN
#include <sunvox.h>

using namespace ableton;
using namespace ableton::linkaudio;

struct Engine
{
    Link link;
    AudioPlatform audioPlatform;

    Engine(double tempo, double quantum, std::chrono::microseconds latency) : link(tempo), audioPlatform(link)
    {
        link.enable(true);
        audioPlatform.mEngine.setQuantum(quantum);
        audioPlatform.mEngine.setLatency(latency);
    }
};

PYBIND11_MODULE(audio_engine, m)
{
    using namespace pybind11;

    m.def("init_sunvox", [](const char *sunvox_project_name) {
        if (sv_load_dll())
        {
            exit(1);
        }
        if (sv_init(NULL, 44100, 2, SV_INIT_FLAG_USER_AUDIO_CALLBACK | SV_INIT_FLAG_AUDIO_FLOAT32) < 0)
        {
            sv_unload_dll();
            exit(2);
        }
        sv_open_slot(0);
        if (sv_load(0, sunvox_project_name))
        {
            sv_close_slot(0);
            sv_deinit();
            sv_unload_dll();
            exit(3);
        }
        sv_volume(0, 256);
    });

    class_<Engine>(m, "Engine")
        .def(init<double, double, std::chrono::microseconds>())
        .def("start", [](Engine &engine) {
            engine.audioPlatform.mEngine.startPlaying();
        })
        .def("stop", [](Engine &engine) {
            engine.audioPlatform.mEngine.stopPlaying();
        })
        .def("setTempo", [](Engine &engine, double tempo) {
            engine.audioPlatform.mEngine.setTempo(tempo);
        })
        .def("setLatency", [](Engine &engine, std::chrono::microseconds latency) {
            engine.audioPlatform.mEngine.setLatency(latency);
        })
        .def("getState", [](Engine &engine) {
            auto time = engine.link.clock().micros();
            auto sessionState = engine.link.captureAppSessionState();
            auto quantum = engine.audioPlatform.mEngine.quantum();
            auto beat = sessionState.beatAtTime(time, quantum);
            auto phase = beat < 0. ? beat : sessionState.phaseAtTime(time, quantum);
            return make_tuple(sessionState.tempo(), phase);
        });
}
