"""Run/resume bounded immutable causal experiments; see docs/EXPERIMENTS.md."""
import argparse
from app.evaluation.reproducible import run_causal


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--subjects", help="Comma-separated subject IDs")
    parser.add_argument("--models", default="logistic_regression,linear_svm,random_forest")
    parser.add_argument("--windows", default="20,40,60,80,100,120,160,200,400")
    parser.add_argument("--evaluation", choices=["holdout", "loso"], default="loso")
    parser.add_argument("--smoke", action="store_true")
    parser.add_argument("--serve", action="store_true")
    parser.add_argument("--matched-reference", action="store_true")
    parser.add_argument("--resume", help="Existing incomplete experiment ID")
    args = parser.parse_args()
    result = run_causal(subjects=args.subjects.split(",") if args.subjects else None,
                        models=args.models.split(","), windows=[int(w) for w in args.windows.split(",")],
                        evaluation=args.evaluation, smoke=args.smoke, serve=args.serve, experiment_id=args.resume, matched_reference=args.matched_reference,
                        progress=lambda **kw: print(kw, flush=True))
    print("Experiment:", result["experiment_id"], flush=True)
    for r in result["results"]:
        print(r["model_name"], r["window_ms"], r["metrics"]["accuracy"], r["metrics"]["macro_f1"])


if __name__ == "__main__":
    main()
