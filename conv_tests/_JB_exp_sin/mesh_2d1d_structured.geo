DefineConstant[ d = { $d$ , Name "Gmsh/Parameters/d"}];
DefineConstant[ h = { $h$ , Name "Gmsh/Parameters/h"}];
Point(1) = {-1+d/2, 0, 0, h};
Point(2) = {-1+d/2, 1, 0, h};
Line(1) = {1, 2};

Extrude{ 1-d/2, 0, 0 }{ Line{1}; Layers{(2-d)/2/h}; }
Extrude{ 1-d/2, 0, 0 }{ Line{2}; Layers{(2-d)/2/h}; }

Physical Surface("hornina") = { 5, 9};
Physical Line("puklina") = { 2 };
Physical Line(".right") = { 6 };
Physical Line(".left") = { 1 };
Physical Line(".no_flow") = { 3, 4, 7, 8 };
Physical Point(".no_flow_body") = { 3, 4 };
