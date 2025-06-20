

import Parameter

class ParameterDatabase:
    def __init__(self, filename):
        self.params = {}
        self._load(filename)

    def _load(self, filename):
        with open(filename, 'r') as f:
            for line in f:
                # Strip comments and whitespace
                line = line.split("#")[0].strip()
                if not line:
                    continue
                if "=" not in line:
                    raise ValueError(f"Invalid line in parameter file: {line}")
                key, value = map(str.strip, line.split("=", 1))
                self.params[key] = value

    def getParamValue(self, param:Parameter, default:Parameter=None):
        if self.exists(param):
            return self.params.get(param)
        else:
            if self.exists(default):
                return self.params.get(param)
            else:
                return None

    def getString(self, param:Parameter, default:Parameter=None)->str:
        return str(self.getParamValue(param, default))

    def getInt(self, param:Parameter, default_param:Parameter=None)->int:
        val = self.getParamValue(param, default_param)

        if val is not None:
            return int(val) 
        else:
            raise SystemExit(f"Fatal error: cannot find the parameter either {param} or {default_param}")

    def getDoubleWithDefault(self, param:Parameter, default_param:Parameter, default_val)->float:

        val = self.getParamValue(param, default_param)
        return float(val) if val is not None else default_val

    def getInstanceForParameter(self, param:Parameter, default_param:Parameter, cls_type):
        
        class_name = self.getParamValue(param, default_param)
        if class_name is None:
            raise ValueError(f"Parameter '{param}' is not defined.")
        
        components = class_name.split('.')
        
        module = __import__(".".join(components[:-1]), fromlist=[components[-1]])
        return getattr(module, components[-1])()

    def exists(self, param:Parameter, default:Parameter=None)->bool:
        return param in self.params
    

if __name__ == "__main__":
    db = ParameterDatabase('D:\\zhixing\\科研\\LGP4PY\\deap_LGP\\tasks\\Symbreg\\parameters\\simpleLGP_SRMT.params')
    param = Parameter.Parameter("stat").push("child").push("0")
    test = db.getParamValue(str(param))  # returns value
    print(test)
    print(db)
