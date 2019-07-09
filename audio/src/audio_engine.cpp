#include "AudioPlatform.hpp"
#include <pybind11/pybind11.h>
#include <pybind11/functional.h>

using namespace ableton;
using namespace ableton::linkaudio;

struct Engine {
  Link link;
  AudioPlatform audioPlatform;

  Engine(double tempo, double quantum): link(tempo), audioPlatform(link) {
    link.enable(true);
    audioPlatform.mEngine.setQuantum(quantum);
  }
};

PYBIND11_MODULE(audio_engine, m) {
  using namespace pybind11;

  class_<Engine>(m, "Engine")
    .def(init<double, double>())
    .def("start", [](Engine& engine) {
      engine.audioPlatform.mEngine.startPlaying();
    })
    .def("stop", [](Engine& engine) {
      engine.audioPlatform.mEngine.stopPlaying();
    })
    .def("setTempo", [](Engine& engine, double tempo) {
      engine.audioPlatform.mEngine.setTempo(tempo);
    })
    .def("getState", [](Engine& engine) {
      auto time = engine.link.clock().micros();
      auto sessionState = engine.link.captureAppSessionState();
      auto quantum = engine.audioPlatform.mEngine.quantum();
	  auto beat = sessionState.beatAtTime(time, quantum);
      auto phase = beat < 0. ? beat : sessionState.phaseAtTime(time, quantum);
      return make_tuple(sessionState.tempo(), phase);
    });
}
