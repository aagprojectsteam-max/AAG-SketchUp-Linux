# Original geometry fixture. Load in a fresh, unsaved, empty SketchUp model only.
# Actual mouse/tool tests remain separate manual acceptance gates.
module AAGUpdateFixture
  def self.create
    started = false
    model = Sketchup.active_model
    raise 'Use a new, unsaved, empty model' unless model.path.empty? && model.entities.empty?
    model.start_operation('AAG update fixture', true)
    started = true
    group = model.entities.add_group
    face = group.entities.add_face([0,0,0], [120,0,0], [120,96,0], [0,96,0])
    face.reverse! if face.normal.z < 0
    face.pushpull(100)
    model.entities.add_line([160,0,0], [240,90,60])
    model.set_attribute('AAGUpdateFixture', 'schema', 1)
    model.commit_operation
    started = false
    model.active_view.zoom_extents
    summary
  rescue StandardError
    model.abort_operation if started
    raise
  end

  def self.summary
    model = Sketchup.active_model
    raise 'Not an AAG test fixture' unless model.get_attribute('AAGUpdateFixture', 'schema') == 1
    group = model.entities.grep(Sketchup::Group).first
    { edges: group.entities.grep(Sketchup::Edge).length,
      faces: group.entities.grep(Sketchup::Face).length,
      dimensions: [group.bounds.width, group.bounds.height, group.bounds.depth].map(&:to_f),
      loose_edges: model.entities.grep(Sketchup::Edge).length }
  end
end
# Run AAGUpdateFixture.create explicitly, then Save As a NEW private test path.
# Expected: edges 12, faces 6, dimensions [120, 96, 100], loose_edges 1.
