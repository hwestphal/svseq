#include "AudioPlatform.hpp"
#include <pybind11/pybind11.h>
#include <pybind11/functional.h>
#include <pybind11/chrono.h>
#include <pybind11/stl.h>

#define SUNVOX_MAIN
#if defined(__linux__) || defined(linux)
#include <dlfcn.h>
#endif
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

    m.def("init_sunvox", [](list instruments, int vol) {
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
        for (int i = 0; i < instruments.size(); i++)
        {
            auto const path = PyUnicode_AsUTF8(instruments[i].ptr());
            if (path[0])
            {
                auto const m = sv_load_module(0, path, 0, 0, 0);
                if (m < 1)
                {
                    sv_close_slot(0);
                    sv_deinit();
                    sv_unload_dll();
                    exit(3);
                }
                sv_lock_slot(0);
                sv_connect_module(0, m, 0);
                sv_unlock_slot(0);
            }
            else
            {
                sv_load_module_from_memory(0, 0, 0, 0, 0, 0);
            }
        }
        sv_volume(0, vol);
    });

    class_<Engine>(m, "Engine")
        .def(init<double, double, std::chrono::microseconds>())
        .def("start", [](Engine &engine, bool metronome) {
            engine.audioPlatform.mEngine.startPlaying(metronome);
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
        .def("setQuantum", [](Engine &engine, double quantum) {
            engine.audioPlatform.mEngine.setQuantum(quantum);
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
        .def("sendNotes", [](Engine &engine, int track_num, int note0, int note1, int note2, int note3, int vel, int module) {
            sv_lock_slot(0);
            sv_send_event(0, track_num * 4, note0, vel, module, 0, 0);
            sv_send_event(0, track_num * 4 + 1, note1, vel, module, 0, 0);
            sv_send_event(0, track_num * 4 + 2, note2, vel, module, 0, 0);
            sv_send_event(0, track_num * 4 + 3, note3, vel, module, 0, 0);
            sv_unlock_slot(0);
        })
        .def("sendNoteOff", [](Engine &engine, int track_num, int module) {
            sv_lock_slot(0);
            sv_send_event(0, track_num * 4, 128, 0, module, 0, 0);
            sv_send_event(0, track_num * 4 + 1, 128, 0, module, 0, 0);
            sv_send_event(0, track_num * 4 + 2, 128, 0, module, 0, 0);
            sv_send_event(0, track_num * 4 + 3, 128, 0, module, 0, 0);
            sv_unlock_slot(0);
        })
        .def("setCtls", [](Engine &engine, int module, const std::tuple<int, int, int, int> &ctls) {
            sv_send_event(0, 0, 0, 0, module, 0x0600, std::get<0>(ctls));
            sv_send_event(0, 0, 0, 0, module, 0x0700, std::get<1>(ctls));
            sv_send_event(0, 0, 0, 0, module, 0x0800, std::get<2>(ctls));
            sv_send_event(0, 0, 0, 0, module, 0x0900, std::get<3>(ctls));
        })
        .def("getCtls", [](Engine &engine) {
            list vll;
            for (int i = 1; i <= 128; i++)
            {
                list vl;
                for (int j = 5; j <= 8; j++)
                {
                    vl.append(sv_get_module_ctl_value(0, i, j, 1));
                }
                vll.append(vl);
            }
            return vll;
        });
}
