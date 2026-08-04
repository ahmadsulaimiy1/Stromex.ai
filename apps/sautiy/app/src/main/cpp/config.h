/*
 * Minimal LAME configuration for Android.
 *
 * LAME normally generates this with autoconf, which we do not run. Supplying it by hand is the
 * standard approach for NDK builds and keeps the result reproducible across NDK versions.
 *
 * Note the trap this replaces: passing -DHAVE_CONFIG_H=0 on the command line does NOT disable
 * the include, because LAME tests it with `#ifdef`, which is true for any definition including
 * zero. The header must either exist or the macro must be absent entirely.
 */
#ifndef SAUTIY_LAME_CONFIG_H
#define SAUTIY_LAME_CONFIG_H

#define STDC_HEADERS 1
#define HAVE_LIMITS_H 1
#define HAVE_STRING_H 1
#define HAVE_STDLIB_H 1
#define HAVE_ERRNO_H 1
#define HAVE_FCNTL_H 1
#define HAVE_INTTYPES_H 1
#define HAVE_STDINT_H 1
#define HAVE_SYS_TYPES_H 1
#define HAVE_UNISTD_H 1
#define HAVE_MEMCPY 1
#define HAVE_STRCHR 1

/* Single-precision throughout: the phone has no use for the double-precision paths. */
#define ieee754_float32_t float

/* LAME's fast float-to-int rounding. Valid on every ABI the NDK targets. */
#define TAKEHIRO_IEEE754_HACK 1

#define PACKAGE "lame"
#define VERSION "3.100"
#define LAME_LIBRARY_BUILD 1

/*
 * mpglib is LAME's *decoder*. SAUTIY only encodes, so it is left out entirely — which also
 * means mpglib_interface.c must not be in the source list.
 */
#undef HAVE_MPGLIB

#endif
