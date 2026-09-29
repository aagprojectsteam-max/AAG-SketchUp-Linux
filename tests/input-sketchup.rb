# Original, manual Unicode probe. Does not inspect or modify the open model.
require 'json'
module AAGBilingualProbe
  def self.run(new_private_directory)
    raise 'Use a new private output directory' if File.exist?(new_private_directory)
    Dir.mkdir(new_private_directory)
    writer = lambda do |name, values|
      File.write(File.join(new_private_directory, name + '.json'),
                 JSON.pretty_generate(values: values, codepoints: values.map(&:codepoints)))
    end
    labels = ['English 1', 'Hebrew 1', 'English 2', 'Hebrew 2']
    values = UI.inputbox(labels, ['', '', '', ''], 'AAG bilingual Qt input test')
    writer.call('qt', values) if values
    @dialog = UI::HtmlDialog.new(dialog_title: 'AAG bilingual CEF input test',
                                 width: 700, height: 450)
    @dialog.add_action_callback('record') do |_, data|
      writer.call('cef', JSON.parse(data))
    end
    @dialog.set_html(<<~HTML)
      <!doctype html><meta charset="utf-8">
      <style>body{font:22px sans-serif}input{font:24px sans-serif;width:90%;margin:8px}</style>
      <h3>Use harmless test phrases only</h3>
      <input autofocus placeholder="English 1"><input placeholder="Hebrew 1">
      <input placeholder="English 2"><input placeholder="Hebrew 2">
      <script>
      const fields = [...document.querySelectorAll('input')];
      fields.forEach(field => field.addEventListener('input', () =>
        sketchup.record(JSON.stringify(fields.map(x => x.value)))));
      </script>
    HTML
    @dialog.show
  end
end
