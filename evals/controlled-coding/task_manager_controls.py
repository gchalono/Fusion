"""FNXC:TaskManagerIntegration 2026-11-09-19:53:
Repeatable TEST DOUBLE partial grading controls only. This is not an A/B/C coding
runner or model capability benchmark. Never supplies reference code to a treatment.
"""
import argparse
import json
from pathlib import Path
from task_manager_grader import grade
from task_manager_adapter import sha

CONTROLS={
 'known-incorrect':"from http.server import HTTPServer,BaseHTTPRequestHandler\nclass H(BaseHTTPRequestHandler):\n def do_GET(self):\n  self.send_response(200);self.end_headers();self.wfile.write(b'<script></script><button>Task</button>')\nHTTPServer(('127.0.0.1',8080),H).serve_forever()\n",
 'hidden-test-tampering':"from pathlib import Path\ntry: Path('/eval/task_manager_grader.py').write_text('print(\"success\")')\nexcept OSError: pass\nprint('TEST DOUBLE fabricated success after tampering attempt')\n",
 'fabricated-success':"print('{\"success\":true,\"tests\":999}')\n"}


def controls(root):
 root=Path(root);root.mkdir(parents=True,exist_ok=False)
 reference=Path(__file__).with_name('task_manager_reference.py')
 # Normalization declared before comparison: grading record only; omit paths,
 # process timing, transport metadata. No patch or Pi reproducibility is claimed.
 results={'reference':grade(reference,root/'reference')}
 for name,source in CONTROLS.items():
  file=root/(name+'.py');file.write_text(source)
  results[name]=grade(file,root/name)
 repeat=grade(reference,root/'reference-repeat')
 positive=results['reference']['success'] and repeat['success']
 negative=all(results[n]['success'] is False for n in CONTROLS)
 normalized=lambda x:{k:x[k] for k in ('classification','success','checks','unverified')}
 record={'classification':'TEST DOUBLE ACCEPTANCE CONTROLS; NOT NATIVE ARM RUNS',
         'results':results,'positive_reference_passed':positive,'negative_controls_rejected':negative,
         'normalized_reference_observations_equal':normalized(repeat)==normalized(results['reference']),
         'successful_reference_reproducibility':positive and normalized(repeat)==normalized(results['reference']),
         'reference_repeat':repeat,'reference_source_sha256':sha(reference.read_bytes()),
         'unverified':['complete native arm repeat','general candidate interface adapter','universal candidate test-quality proof'],
         'provider_contacts':0,'Pi_sessions':0}
 (root/'results.json').write_text(json.dumps(record,indent=2)+'\n')
 return record

if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--out',type=Path,required=True);a=p.parse_args();result=controls(a.out);print(json.dumps(result));raise SystemExit(not(result['positive_reference_passed'] and result['negative_controls_rejected']))
