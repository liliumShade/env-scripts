#! /usr/bin/env python3
import argparse
import os
import re


SPEC2006_BASE_PATH = os.environ.get(
    "SPEC2006_BENCHSPEC_DIR",
    "/nfs/home/share/cpu2006v99/benchspec/CPU2006",
)
SPEC2017_BASE_PATH = os.environ.get(
    "SPEC2017_BENCHSPEC_DIR",
    "/nfs/home/share/spec2017_slim/benchspec/CPU",
)

SPEC2006_INT = [
    "400.perlbench",
    "401.bzip2",
    "403.gcc",
    "429.mcf",
    "445.gobmk",
    "456.hmmer",
    "458.sjeng",
    "462.libquantum",
    "464.h264ref",
    "471.omnetpp",
    "473.astar",
    "483.xalancbmk",
]

SPEC2006_FP = [
    "410.bwaves",
    "416.gamess",
    "433.milc",
    "434.zeusmp",
    "435.gromacs",
    "436.cactusADM",
    "437.leslie3d",
    "444.namd",
    "447.dealII",
    "450.soplex",
    "453.povray",
    "454.Calculix",
    "459.GemsFDTD",
    "465.tonto",
    "470.lbm",
    "481.wrf",
    "482.sphinx3",
]

SPEC2017_INT = {
    "rate": [
        "500.perlbench_r",
        "502.gcc_r",
        "505.mcf_r",
        "520.omnetpp_r",
        "523.xalancbmk_r",
        "525.x264_r",
        "531.deepsjeng_r",
        "541.leela_r",
        "548.exchange2_r",
        "557.xz_r",
    ],
    "speed": [
        "600.perlbench_s",
        "602.gcc_s",
        "605.mcf_s",
        "620.omnetpp_s",
        "623.xalancbmk_s",
        "625.x264_s",
        "631.deepsjeng_s",
        "641.leela_s",
        "648.exchange2_s",
        "657.xz_s",
    ],
}

SPEC2017_FP = {
    "rate": [
        "503.bwaves_r",
        "507.cactuBSSN_r",
        "508.namd_r",
        "510.parest_r",
        "511.povray_r",
        "519.lbm_r",
        "521.wrf_r",
        "526.blender_r",
        "527.cam4_r",
        "538.imagick_r",
        "544.nab_r",
        "549.fotonik3d_r",
        "554.roms_r",
    ],
    "speed": [
        "603.bwaves_s",
        "607.cactuBSSN_s",
        "619.lbm_s",
        "621.wrf_s",
        "627.cam4_s",
        "628.pop2_s",
        "638.imagick_s",
        "644.nab_s",
        "649.fotonik3d_s",
        "654.roms_s",
    ],
}


def normalize_spec_mode(spec_mode):
    mode = (spec_mode or "speed").lower()
    if mode not in ("speed", "rate"):
        raise ValueError(f"unknown SPEC mode: {spec_mode}")
    return mode


def _benchmark_base(name):
    base = name.lower()
    if base.endswith(("_r", "_s")):
        base = base[:-2]
    if "." in base:
        base = base.split(".", 1)[1]
    return base


def _benchmark_matches(benchspec, dirname, suffix=None):
    dirname_lower = dirname.lower()
    if suffix is not None and not dirname_lower.endswith(suffix):
        return False

    benchspec_lower = benchspec.lower()
    if benchspec_lower in dirname_lower:
        return True

    return _benchmark_base(benchspec_lower) == _benchmark_base(dirname_lower)


def _listdir(path):
    if not os.path.isdir(path):
        return []
    return sorted(os.listdir(path))


def _last_number(line):
    matches = re.findall(r"[-+]?\d+(?:\.\d+)?", line)
    if not matches:
        return None
    return int(float(matches[-1]))


def _read_first_reftime(path, preferred_key=None):
    if not os.path.isfile(path):
        return None

    with open(path) as f:
        lines = f.readlines()

    if preferred_key is not None:
        key = preferred_key.lower()
        for line in lines:
            if key in line.lower():
                value = _last_number(line)
                if value is not None:
                    return value

    for line in lines:
        value = _last_number(line)
        if value is not None:
            return value
    return None


def _read_last_reftime(path):
    if not os.path.isfile(path):
        return None

    with open(path) as f:
        lines = f.readlines()

    for line in reversed(lines):
        value = _last_number(line)
        if value is not None:
            return value
    return None


def _find_spec2006_dir(benchspec):
    for dirname in _listdir(SPEC2006_BASE_PATH):
        if _benchmark_matches(benchspec, dirname):
            return dirname
    return None


def _find_spec2017_dir(benchspec, spec_mode):
    suffix = "_s" if normalize_spec_mode(spec_mode) == "speed" else "_r"
    for dirname in _listdir(SPEC2017_BASE_PATH):
        if _benchmark_matches(benchspec, dirname, suffix):
            return dirname
    return None


def _get_spec2017_reftime(benchspec, spec_mode):
    mode = normalize_spec_mode(spec_mode)
    data_set = "refspeed" if mode == "speed" else "refrate"
    dirname = _find_spec2017_dir(benchspec, mode)

    if dirname is not None:
        reftime_path = os.path.join(
            SPEC2017_BASE_PATH, dirname, "data", data_set, "reftime"
        )
        reftime = _read_first_reftime(reftime_path, data_set)
        if reftime is not None:
            return reftime

    if mode == "speed":
        paired_rate_dir = _find_spec2017_dir(benchspec, "rate")
        if paired_rate_dir is not None:
            for fallback_data_set in ("refspeed", "refrate"):
                reftime_path = os.path.join(
                    SPEC2017_BASE_PATH,
                    paired_rate_dir,
                    "data",
                    fallback_data_set,
                    "reftime",
                )
                reftime = _read_first_reftime(reftime_path, "refspeed")
                if reftime is not None:
                    return reftime

    return None


def get_spec_reftime(benchspec, spec_version, spec_mode="speed"):
    if spec_version == 2006:
        dirname = _find_spec2006_dir(benchspec)
        if dirname is not None:
            reftime_path = os.path.join(SPEC2006_BASE_PATH, dirname, "data/ref/reftime")
            reftime = _read_last_reftime(reftime_path)
            if reftime is not None:
                return reftime
    elif spec_version == 2017:
        reftime = _get_spec2017_reftime(benchspec, spec_mode)
        if reftime is not None:
            return reftime

    mode_text = f" {spec_mode}" if spec_version == 2017 else ""
    print(f"do not find reftime for {benchspec} {spec_version}{mode_text}")
    return None


def get_spec_int(spec_version, spec_mode="speed"):
    if spec_version == 2006:
        return SPEC2006_INT
    if spec_version == 2017:
        return SPEC2017_INT[normalize_spec_mode(spec_mode)]
    return None


def get_spec_fp(spec_version, spec_mode="speed"):
    if spec_version == 2006:
        return SPEC2006_FP
    if spec_version == 2017:
        return SPEC2017_FP[normalize_spec_mode(spec_mode)]
    return None


def _format_float(value, width):
    if value is None:
        return f"{'NaN':>{width}}"
    return f"{value:>{width}.3f}"


def _format_int(value, width):
    if value is None:
        return f"{'NaN':>{width}}"
    return f"{value:>{width}d}"


def _print_score_table(rows):
    label_width = max(15, *(len(row["name"]) for row in rows))
    print(
        f"{'':>{label_width}} {'time':>8} {'ref_time':>8} {'score':>6} {'coverage':>8}"
    )
    for row in rows:
        print(
            f"{row['name']:>{label_width}} "
            f"{_format_float(row.get('time'), 8)} "
            f"{_format_int(row.get('ref_time'), 8)} "
            f"{_format_float(row.get('score'), 6)} "
            f"{_format_float(row.get('coverage'), 8)}"
        )


def _append_suite_rows(rows, benchspec_list, spec_score, spec_weight, frequency):
    suite_score = 1
    for benchspec in benchspec_list:
        found_name = None
        for name in spec_score:
            if name.lower() in benchspec.lower():
                found_name = name
                break

        if found_name is None:
            rows.append(
                {
                    "name": benchspec,
                    "time": None,
                    "ref_time": None,
                    "score": None,
                    "coverage": 0.0,
                }
            )
            continue

        info = spec_score[found_name]
        score_per_ghz = info["score"] / frequency
        suite_score *= score_per_ghz
        rows.append(
            {
                "name": benchspec,
                "time": info["time"],
                "ref_time": info["ref_time"],
                "score": score_per_ghz,
                "coverage": spec_weight.get(found_name) if spec_weight else None,
            }
        )

    return suite_score ** (1 / len(benchspec_list))


def get_spec_score(spec_time, spec_version, frequency, spec_weight=None, spec_mode="speed"):
    print("==================== Score ===================")
    total_count = 0
    total_score = 1
    spec_score = dict()
    for spec_name in spec_time:
        reftime = get_spec_reftime(spec_name, spec_version, spec_mode)
        if reftime is None:
            continue
        score = reftime / spec_time[spec_name]
        total_count += 1
        total_score *= score / frequency
        spec_score[spec_name] = {
            "time": spec_time[spec_name],
            "ref_time": reftime,
            "score": score,
        }

    if total_count == 0:
        print(f"SPEC{spec_version}/GHz:     N/A")
        print(f"SPEC{spec_version}@{frequency}GHz:    N/A")
        return

    geomean_score_per_ghz = total_score ** (1 / total_count)
    rows = []
    specint_list = get_spec_int(spec_version, spec_mode)
    geomean_specint_score = _append_suite_rows(
        rows, specint_list, spec_score, spec_weight or {}, frequency
    )
    rows.append(
        {
            "name": f"SPECint{spec_version}/GHz",
            "time": None,
            "ref_time": None,
            "score": geomean_specint_score,
            "coverage": None,
        }
    )

    specfp_list = get_spec_fp(spec_version, spec_mode)
    geomean_specfp_score = _append_suite_rows(
        rows, specfp_list, spec_score, spec_weight or {}, frequency
    )
    rows.append(
        {
            "name": f"SPECfp{spec_version}/GHz",
            "time": None,
            "ref_time": None,
            "score": geomean_specfp_score,
            "coverage": None,
        }
    )
    rows.append(
        {
            "name": f"SPEC{spec_version}/GHz",
            "time": None,
            "ref_time": None,
            "score": geomean_score_per_ghz,
            "coverage": None,
        }
    )

    _print_score_table(rows)
    print()
    print(f"SPEC{spec_version}/GHz:  {geomean_score_per_ghz:6.3f}")
    print(f"SPEC{spec_version}@{frequency}GHz: {geomean_score_per_ghz * frequency:6.3f}")
    print()


def get_spec_time(csv_path):
    def to_seconds(s):
        hours, minutes, seconds = s.split(":")
        return 3600 * int(hours) + 60 * int(minutes) + int(seconds)

    spec_time = {}
    with open(csv_path, "r") as f:
        for line in f:
            items = line.strip().split(",")
            if not items:
                continue
            if len(items) == 3:
                name, start_time, finish_time = items
                spec_name = name.split("_")[0]
                num_seconds = to_seconds(finish_time) - to_seconds(start_time)
                spec_time[spec_name] = spec_time.get(spec_name, 0) + num_seconds
    return spec_time


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="spec score scripts")
    parser.add_argument("csv_path", metavar="csv_path", type=str, help="path to spec time csv")
    parser.add_argument("--version", default=2006, type=int, help="SPEC version")
    parser.add_argument("--frequency", default=1, type=float, help="CPU frequency")
    parser.add_argument(
        "--mode",
        default="speed",
        choices=["speed", "rate"],
        help="SPEC2017 mode",
    )

    args = parser.parse_args()

    spec_time = get_spec_time(args.csv_path)
    get_spec_score(spec_time, args.version, args.frequency, spec_mode=args.mode)
