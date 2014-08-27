
pycgen
------

This script allows you to embed Python in your C-style comments that generates code right after the comment. You can add comments to your file:

	/*$pycgen
		dot = """
		inline cmp_math_fn T dot(T2 a, T2 b)
		{
			return a.x * b.x + a.y * b.y;
		}
		"""

		EmitRepl(dot2, "T:float,double,short,int")
	*/

Run the script with:

	pycgen.py <input_filename> <output_filename>

The input file is copied verbatim to the output file with the following generated code next to it:

	/*$pycgen
		dot = """
		inline cmp_math_fn T dot(T2 a, T2 b)
		{
			return a.x * b.x + a.y * b.y;
		}
		"""

		EmitRepl(dot2, "T:float,double,int,short")
	*/
	//$pycgen-begin
		inline cmp_math_fn float dot(float2 a, float2 b)
		{
			return a.x * b.x + a.y * b.y;
		}
		inline cmp_math_fn double dot(double2 a, double2 b)
		{
			return a.x * b.x + a.y * b.y;
		}
		inline cmp_math_fn short dot(short2 a, short2 b)
		{
			return a.x * b.x + a.y * b.y;
		}
		inline cmp_math_fn int dot(int2 a, int2 b)
		{
			return a.x * b.x + a.y * b.y;
		}
	//$pycgen-end

You can see an example of its use at-large in ComputeBridge, here: https://github.com/Celtoys/ComputeBridge/blob/master/cbpp/inc/cbpp/Math.h

This is great for simulating generics in situations when you can't use a language with them. The benefits are:

* Much friendlier and far more powerful than the embedded C pre-processor.
* Allows 3rd parties to use your code without requiring this script.
* Visible code foot-print for all explicitly generated instantiations (unlike C++ templates).
* Each implementation can be stepped-through in a debugger.

Some drawbacks:

* Requires the pre-process on your code. Should be fast enough though, given the script exempts large swathes of code looking for the gen signature.
* Obviously not as good as a decent generics implementation for your language.
