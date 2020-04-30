#include "AudioPlatform.hpp"
#include <pybind11/pybind11.h>
#include <pybind11/functional.h>
#include <pybind11/chrono.h>
#include <pybind11/stl.h>

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
            sv_stop(0);
        })
        .def("setTempo", [](Engine &engine, double tempo) {
            engine.audioPlatform.mEngine.setTempo(tempo);
        })
        .def("setLatency", [](Engine &engine, std::chrono::microseconds latency) {
            engine.audioPlatform.mEngine.setLatency(latency);
        })
        .def("getState", [](Engine &engine) {
            auto time = engine.link.clock().micros() + engine.audioPlatform.mEngine.latency();
            auto sessionState = engine.link.captureAppSessionState();
            auto quantum = engine.audioPlatform.mEngine.quantum();
            auto beat = sessionState.beatAtTime(time, quantum);
            return make_tuple(sessionState.tempo(), beat);
        })
        .def("setEvents", [](Engine &engine, std::vector<std::tuple<int, int, int, int, int, int>> &events) {
            engine.audioPlatform.mEngine.setEvents(events);
        })
        .def("sendNote", [](Engine &engine, int track_num, int note, int vel, int module) {
            sv_lock_slot(0);
            sv_send_event(0, track_num, note, vel, module, 0, 0);
            sv_unlock_slot(0);
        })
        .def("sendNoteOff", [](Engine &engine, int track_num, int module) {
            sv_lock_slot(0);
            sv_send_event(0, track_num, 128, 0, module, 0, 0);
            sv_unlock_slot(0);
        });
}
