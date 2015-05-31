DefineConstant[ d = { $d$ , Name "Gmsh/Parameters/d"}];
DefineConstant[ h = { $h$ , Name "Gmsh/Parameters/h"}];

Point(1) = {-1, 0, 0, h};
Point(2) = {-1, 1, 0, h};
Line(1) = {1, 2};

Extrude{ (2-d)/2, 0, 0 }{ Line{1}; Layers{(2-d)/2/h}; }
Extrude{ d, 0, 0 }{ Line{2}; Layers{d/h}; }
Extrude{ (2-d)/2, 0, 0 }{ Line{6}; Layers{(2-d)/2/h}; }

Physical Surface("hornina") = { 5, 13};
Physical Surface("puklina") = { 9 };
Physical Line(".right") = { 10 };
Physical Line(".left") = { 1 };
Physical Line(".no_flow") = { 3, 4, 11, 12 };
Physical Line(".no_flow_body") = { 7, 8 };
