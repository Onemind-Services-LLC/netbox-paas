var c = jelastic.environment.control, e = envName, s = session, r, resp;

resp = c.GetEnvInfo(e, s);
if (resp.result != 0) return resp;

r = c.RestartNodes({ envName: e, session: s, nodeGroup: nodeGroup, isSequential: false });
if (r.result != 0) return r;

return { result: 0, message: 'Restarted ' + nodeGroup}
