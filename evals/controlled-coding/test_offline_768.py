import copy,unittest
from offline_output_profile import NAME,ceiling
from task_manager_token_revision import offline_contract
class Offline768Tests(unittest.TestCase):
 def test_defaults_unchanged(self):self.assertEqual(ceiling(offline_contract()),512)
 def test_scoped_arithmetic(self):
  d=offline_contract();d['offline_output_profile']=NAME
  self.assertEqual(ceiling(d,offline=True),768);self.assertEqual(4*(32000+768),131072)
  self.assertLessEqual(131072,d['frozen_coding_token_limit'])
 def test_paid_production_experiment1_and_altered_contracts_fail_closed(self):
  d=offline_contract();d['offline_output_profile']=NAME
  for kwargs in ({},{'offline':True,'paid':True},{'offline':True,'production':True}):
   with self.assertRaises(ValueError):ceiling(d,**kwargs)
  for k,v in {'experiment_id':'Experiment 1','provider_spend_authorized_usd':'0.01','coding_attempts_per_run':5,'aggregate_cap_usd':'6.00','request_seconds':61,'offline_only':False}.items():
   bad=copy.deepcopy(d);bad[k]=v
   with self.assertRaises(ValueError):ceiling(bad,offline=True)
 def test_app_alias_does_not_add_a_host_mount(self):
  import tempfile
  from pathlib import Path
  from isolation import namespace_command
  with tempfile.TemporaryFile() as policy:
   default=namespace_command(None,Path('/tmp/app'),[],seccomp_fd=policy.fileno())
   aliased=namespace_command(None,Path('/tmp/app'),[],seccomp_fd=policy.fileno(),app_alias=True)
  i=aliased.index('--symlink');self.assertEqual(aliased[i:i+3],['--symlink','/work','/app'])
  self.assertEqual(aliased[:i]+aliased[i+3:],default)
 def test_original_application_namespace_keeps_filter_and_hides_assertions(self):
  import tempfile
  from pathlib import Path
  from original_evaluator_adapter import secure_argv
  with tempfile.TemporaryFile() as policy:
   argv=secure_argv(Path('/tmp/TEST_DOUBLE_arm'),['/app/run-tests'],policy)
  for flag in ('--unshare-user','--unshare-net','--unshare-pid','--unshare-ipc','--unshare-uts','--seccomp','--clearenv'):self.assertIn(flag,argv)
  self.assertIn('--cap-drop',argv);self.assertNotIn('/checks',argv)
  at=argv.index('/app');self.assertEqual(argv[at-2],'--ro-bind')
 def test_shared_three_arm_768_reservations_and_restart(self):
  import tempfile
  from pathlib import Path
  from budget import AggregateBudget
  d=offline_contract();d['offline_output_profile']=NAME;self.assertEqual(ceiling(d,offline=True),768)
  with tempfile.TemporaryDirectory() as t:
   p=Path(t)/'shared.db';b=AggregateBudget(p,experiment_contract=d)
   for arm in 'ABC':
    run='phase2m-personal-task-manager:'+arm;b.control_run('coding',run,'start')
    for _ in range(4):b.reserve('coding',run,14029,token_bounds=(32000,768))
    with self.assertRaisesRegex(ValueError,'experiment_request_cap'):b.reserve('coding',run,14029,token_bounds=(32000,768))
   self.assertEqual(AggregateBudget(p).snapshot()['reserved_exposure_micro_usd'],168348)
 def test_profile_cannot_change_model_or_mutate_defaults(self):
  import copy
  d=offline_contract();before=copy.deepcopy(d);d['offline_output_profile']=NAME;ceiling(d,offline=True)
  self.assertEqual({k:v for k,v in d.items() if k!='offline_output_profile'},before)
  for key,value in (('model','unauthorized-model'),('provider','unauthorized-provider')):
   bad=copy.deepcopy(d);bad[key]=value
   with self.assertRaises(ValueError):ceiling(bad,offline=True)
