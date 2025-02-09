import wandb
import os

class WandbLogger:
    def __init__(self, project_name="finest-data-subnet", run_name ="miners-stats"):
        self.project_name = project_name
        self.run_name = run_name
        self.run_id = self._get_or_create_run_id()
        self.run = wandb.init(project=project_name, id=self.run_id, name=self.run_name)
        self.api = wandb.Api()

    def _get_or_create_run_id(self):
   
        run_id = None
        try:
            api = wandb.Api(timeout=60)
            for r in api.runs(f"{self.project_name}", order="-updated_at"):
                if r.name == self.run_name:
                    run_id = r.id
                    break

        except Exception:
            run_id = None

        if run_id is None:
            run_id = wandb.util.generate_id()

        return run_id
    
    def log_wandb(self, data):
        wandb.log(data)

    def get_all_scores(self):
        run = self.api.run(f"{self.project_name}/{self.run_id}")
        history = run.history(pandas=False)
        scores = {}
        for row in history:
            uid = row.get("uid")
            score = row.get("score")
            if uid is not None and score is not None:
                scores[int(uid)] = score 
        return scores 