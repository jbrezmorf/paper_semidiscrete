//DefineConstant[ d = { $d$ , Name "Gmsh/Parameters/d"}];
//DefineConstant[ h = { $h$ , Name "Gmsh/Parameters/h"}];
//DefineConstant[ h1d = { $h1d$ , Name "Gmsh/Parameters/h1d"}];
DefineConstant[ d = { 0.1 , Name "Gmsh/Parameters/d"}];
DefineConstant[ h = { 0.05 , Name "Gmsh/Parameters/h"}];
DefineConstant[ h1d = { 0.01 , Name "Gmsh/Parameters/h1d"}];


Point(1) = {-1, 0, 0, h};
Point(2) = {-1, 1, 0, h};
Line(1) = {1, 2};

alpha=Exp( 1/3 * Log( h/h1d) );
h_2=h1d*alpha;
h_1=h_2*alpha;

a_0=4.0/7.0;
a_1=2.0/7.0;
a_2=1.0/7.0;

Extrude{ (2-d)/2, 0, 0 }{ Line{1}; Layers{ {(2-d)/2 * a_0/h, (2-d)/2 * a_1/h_1, (2-d)/2 * a_2/h_2}, {a_0, a_0+a_1, 1}}; }
Extrude{ d, 0, 0 }{ Line{2}; Layers{d/h1d}; }
Extrude{ (2-d)/2, 0, 0 }{ Line{6}; Layers{ {(2-d)/2 * a_2/h_2, (2-d)/2 * a_1/h_1, (2-d)/2 * a_0/h }, {a_2, a_2+a_1, 1}}; }

Physical Surface("hornina") = { 5, 13};
Physical Surface("puklina") = { 9 };
Physical Line(".right") = { 10 };
Physical Line(".left") = { 1 };
Physical Line(".no_flow") = { 3, 4, 11, 12 };
Physical Line(".no_flow_body") = { 7, 8 };
