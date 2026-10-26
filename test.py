import subprocess
import re

def ehrhart_polynomial(vertices):
    polytope = "POLYTOPE\n" + " ".join(vertices) + "\nEND\n"
    polymake_input = "application 'fan';\n" + "fan::normaliz_command('-EhrhartRing -q -e -l -o -p');\n" + polytope
    p = subprocess.Popen(['polymake', '-'], stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    stdout, stderr = p.communicate(polymake_input.encode())
    if stderr:
        raise ValueError(stderr.decode())
    output = stdout.decode()
    match = re.search(r"Ehrhart Polynomial:(.*)", output)
    if match:
        polynomial = match.group(1).strip()
        return polynomial
    else:
        raise ValueError("Ehrhart polynomial not found in output.")

# Example usage
vertices = ["0 0", "1 0", "1 1", "0 1"]
polynomial = ehrhart_polynomial(vertices)
print(polynomial)
