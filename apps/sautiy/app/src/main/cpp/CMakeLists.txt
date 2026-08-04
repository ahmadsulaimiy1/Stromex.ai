cmake_minimum_required(VERSION 3.22.1)
project(sautiymp3 C)

# LAME is not vendored into this repository. See README.md in this directory for the one
# command that fetches it. The build is written so that its absence is a clean, explanatory
# failure rather than a wall of missing-header errors.
set(LAME_DIR ${CMAKE_CURRENT_SOURCE_DIR}/lame)

if (NOT EXISTS ${LAME_DIR}/libmp3lame/lame.c)
    message(FATAL_ERROR
        "LAME sources were not found at ${LAME_DIR}.\n"
        "MP3 export is optional: build without -DSAUTIY_MP3=ON and the app ships without it.\n"
        "To enable it, follow apps/sautiy/app/src/main/cpp/README.md.")
endif()

set(LAME_SOURCES
    ${LAME_DIR}/libmp3lame/bitstream.c
    ${LAME_DIR}/libmp3lame/encoder.c
    ${LAME_DIR}/libmp3lame/fft.c
    ${LAME_DIR}/libmp3lame/gain_analysis.c
    ${LAME_DIR}/libmp3lame/id3tag.c
    ${LAME_DIR}/libmp3lame/lame.c
    ${LAME_DIR}/libmp3lame/newmdct.c
    ${LAME_DIR}/libmp3lame/presets.c
    ${LAME_DIR}/libmp3lame/psymodel.c
    ${LAME_DIR}/libmp3lame/quantize.c
    ${LAME_DIR}/libmp3lame/quantize_pvt.c
    ${LAME_DIR}/libmp3lame/reservoir.c
    ${LAME_DIR}/libmp3lame/set_get.c
    ${LAME_DIR}/libmp3lame/tables.c
    ${LAME_DIR}/libmp3lame/takehiro.c
    ${LAME_DIR}/libmp3lame/util.c
    ${LAME_DIR}/libmp3lame/vbrquantize.c
    ${LAME_DIR}/libmp3lame/VbrTag.c
    ${LAME_DIR}/libmp3lame/version.c
    ${LAME_DIR}/libmp3lame/mpglib_interface.c
)

add_library(sautiymp3 SHARED sautiy_mp3.c ${LAME_SOURCES})

target_include_directories(sautiymp3 PRIVATE
    ${LAME_DIR}/include
    ${LAME_DIR}/libmp3lame
    ${LAME_DIR}/mpglib
)

target_compile_definitions(sautiymp3 PRIVATE
    HAVE_CONFIG_H=0
    STDC_HEADERS=1
    HAVE_LIMITS_H=1
    HAVE_STRING_H=1
    HAVE_MEMCPY=1
    # LAME's own float type. Fixing it here rather than relying on a generated config.h keeps
    # the build reproducible across NDK versions.
    FLOAT8=float
    real=float
)

target_compile_options(sautiymp3 PRIVATE
    -O3
    -ffast-math
    -fvisibility=hidden
    -Wno-unused-variable
    -Wno-unused-but-set-variable
    -Wno-pointer-sign
)

# Only the four JNI entry points are exported; everything of LAME's stays internal.
target_link_options(sautiymp3 PRIVATE "-Wl,-z,max-page-size=16384")

find_library(log-lib log)
target_link_libraries(sautiymp3 ${log-lib} m)
